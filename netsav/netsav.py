# -*-coding:Utf-8 -*

# This file is a part of netsav
#
# Copyright (c) 2014-2015 Pierre GINDRAUD
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Main NETSAV module, contains netsav Class
"""

# System imports
import logging
import logging.handlers
import os
import signal
import socket
import sys
import threading

# Projet Imports
from netsav.configparser import NetsavConfigParser
from netsav.trigger.trigger import TriggerLoader
from netsav.server.server import Server
from netsav.client.client import Client

# Global project declarations
system_logger = logging.getLogger('netsav')

class Netsav:
  """Build a program object, run a server and several clientconfiguration file
  
  Configuration are read from the config file given to the constructor
  run a client thread for each client section of the configuration file
  """

  def __init__(self, daemon = False, config = None, log_level = 'INFO'):
    """Constructor : Build the program lead object
    
    @param(boolean) daemon : if the server must daemonize
    @param(string) config : configuration file's path
    @param(string) log_level : the system minimum logging level for put log
                                message
    """
    ## Variables definitions
    self._config_file = config
    self._configparser = NetsavConfigParser(file = config)
    
    self._to_daemon = daemon
    # Local entities
    #  server obj
    self._server = None
    #  client thread list
    self._l_client = []
    self._l_client_name = []
    # log parameters
    self._log_level = None
    self._log_target = None
    # global trigger object to use for client notify
    self._trigger = None
    
    ## Initializing
    # Initialise log system
    self.setLogLevel(log_level)
    self.setLogTarget('STDOUT')

  def start(self, pidfile):
    """Run the service
    
    Daemonize if daemon is True in constructor
    @param(string) pidfile : pidfile's path
    """
    # Restreint access to only owner
    os.umask(0x0077)
    
    # Installing signal catching function
    signal.signal(signal.SIGTERM, self._sigTERMhandler)
    signal.signal(signal.SIGINT, self._sigTERMhandler)

    # Loading main configuration
    if self._configparser.load() != True:
      system_logger.error("Unable to load configuration from file: %s", 
                                                    self._config_file)
      return False
    self.setLogLevel(self._configparser.getLogLevel())
    self.setLogTarget(self._configparser.getLogTarget())
    if_ignore_own = self._configparser.getOptIgnoreOwn()

    # Turn in daemon mode
    if self._to_daemon:
      system_logger.debug("Starting in daemon mode")
      if self._daemonize():
        system_logger.info("Daemon started")
      else:
        system_logger.error("Could not create daemon")
        raise Exception("Could not create daemon")

    # Create the pid file
    try:
      system_logger.debug("Creating PID file %s", pidfile)
      pid_file = open(pidfile, 'w')
      pid_file.write(str(os.getpid())+'\n')
      pid_file.close()
    except IOError as e:
      system_logger.error("Unable to create PID file: %s", pidfile)

    # Init clients objects
    client_config = self._configparser.getClientConfigDict()
    for name in client_config:
      # Ignore self hostname declaration
      if name == socket.gethostname() and if_ignore_own == True:
        system_logger.debug("Ignoring client %s", name)
      else:
        cli = Client(conf_dict = client_config[name], 
                            trigger = self.getTrigger())
        if self.pushClient(cli):
          system_logger.info("Added client : %s", name)
        else:
          system_logger.error("Failed to add client : %s", name)

    # Init server object
    self._server = Server(conf_dict = self._configparser.getServerConfigDict())
    if self._server.start():
      # Run the main loop
      self.run()

    # Remove the pid file
    try:
      system_logger.debug("Remove PID file %s", pidfile)
      os.remove(pidfile)
    except OSError as e:
      system_logger.error("Unable to remove PID file: %s", e)

    # STOP
    self.stop()
    system_logger.info("Exiting netsav")
    return True

  def run(self):
    """Main loop function
    
    This function is saperated from the start() for old Thread implement needed
    It only provide the main service loop and It is launch by start()
    """
    try:
      if self.hasClient():
        for c in self._l_client:
          c.start()
      self._server.getServerInstance().serve_forever()
    except (KeyboardInterrupt, SystemExit):
      system_logger.error('## Abnormal termination ##')

  def stop(self):
    """ Stop properly the server after signal received
    
    It is call by start() et signalHandling functions
    """
    system_logger.debug('Stoping all subthread')
    for t in threading.enumerate():
      n = t.getName()
      if n != "MainThread":
        t.exit()
    # Close log
    logging.shutdown()


  ###
  ### System running functions
  ###

  def _sigTERMhandler(self, signum, frame):
    """Make the program terminate after receving system signal
    """
    system_logger.debug("Caught system signal %d", signum)
    sys.exit(1)

  def _daemonize(self):
    """Turn the service as a deamon
    
    Detach a process from the controlling terminal
    and run it in the background as a daemon.
    See : http://code.activestate.com/recipes/278731/
    """
    try:
      # Fork a child process so the parent can exit.  This returns control to
      # the command-line or shell.  It also guarantees that the child will not
      # be a process group leader, since the child receives a new process ID
      # and inherits the parent's process group ID.  This step is required
      # to insure that the next call to os.setsid is successful.
      pid = os.fork()
    except OSError as e:
      return ((e.errno, e.strerror))

    if (pid == 0): # The first child.
      # To become the session leader of this new session and the process group
      # leader of the new process group, we call os.setsid().  The process is
      # also guaranteed not to have a controlling terminal.
      os.setsid()

      # Is ignoring SIGHUP necessary?
      #
      # It's often suggested that the SIGHUP signal should be ignored before
      # the second fork to avoid premature termination of the process.  The
      # reason is that when the first child terminates, all processes, e.g.
      # the second child, in the orphaned group will be sent a SIGHUP.
      #
      # "However, as part of the session management system, there are exactly
      # two cases where SIGHUP is sent on the death of a process:
      #
      #   1) When the process that dies is the session leader of a session that
      #      is attached to a terminal device, SIGHUP is sent to all processes
      #      in the foreground process group of that terminal device.
      #   2) When the death of a process causes a process group to become
      #      orphaned, and one or more processes in the orphaned group are
      #      stopped, then SIGHUP and SIGCONT are sent to all members of the
      #      orphaned group." [2]
      #
      # The first case can be ignored since the child is guaranteed not to have
      # a controlling terminal.  The second case isn't so easy to dismiss.
      # The process group is orphaned when the first child terminates and
      # POSIX.1 requires that every STOPPED process in an orphaned process
      # group be sent a SIGHUP signal followed by a SIGCONT signal.  Since the
      # second child is not STOPPED though, we can safely forego ignoring the
      # SIGHUP signal.  In any case, there are no ill-effects if it is ignored.
      #
      # import signal           # Set handlers for asynchronous events.
      # signal.signal(signal.SIGHUP, signal.SIG_IGN)

      try:
         # Fork a second child and exit immediately to prevent zombies.  This
         # causes the second child process to be orphaned, making the init
         # process responsible for its cleanup.  And, since the first child is
         # a session leader without a controlling terminal, it's possible for
         # it to acquire one by opening a terminal in the future (System V-
         # based systems).  This second fork guarantees that the child is no
         # longer a session leader, preventing the daemon from ever acquiring
         # a controlling terminal.
         pid = os.fork()  # Fork a second child.
      except OSError as e:
         return ((e.errno, e.strerror))

      if (pid == 0):  # The second child.
         # Since the current working directory may be a mounted filesystem, we
         # avoid the issue of not being able to unmount the filesystem at
         # shutdown time by changing it to the root directory.
         os.chdir("/")
      else:
         # exit() or _exit()?  See below.
         os._exit(0)  # Exit parent (the first child) of the second child.
    else:
      # exit() or _exit()?
      # _exit is like exit(), but it doesn't call any functions registered
      # with atexit (and on_exit) or any registered signal handlers.  It also
      # closes any open file descriptors.  Using exit() may cause all stdio
      # streams to be flushed twice and any temporary files may be unexpectedly
      # removed.  It's therefore recommended that child branches of a fork()
      # and the parent branch(es) of a daemon use _exit().
      os._exit(0) # Exit parent of the first child.

    return True


  ###
  ### Client managment functions
  ###
  
  def pushClient(self, client):
    """Add a client object to the internal used list
    
    Add a client to the list, it should not already exist
    otherwise it will not be added
    @param(Client) : the client object to add to the list
    @return(boolean) : True if add success
                        False otherwise
    """
    if not client.check():
      return False
    if client.getName() not in self._l_client_name:
      self._l_client.append(client)
      self._l_client_name.append(client.getName())
      return True
    else:
      return False

  def hasClient(self):
    """Check if there is/are registered clients
    
    @return(boolean) : True if list contains at least one client
                       False otherwise
    """
    if len(self._l_client) > 0:
      return True
    else:
      return False

  ###
  ### Trigger
  ###
  def getTrigger(self):
    """Return the instance of the trigger object
    
    @return(netsav.Trigger) if config is being loaded
                None otherwise
    """
    if not self._configparser.isLoaded():
      return None
    if self._trigger is None :
      t = TriggerLoader('Trigger', configparser = self._configparser)
      if t.load():
        self._trigger = t
    return self._trigger

  ###
  ### Logging functions
  ###

  def setLogLevel(self, value):
    """Set the logging level.
    
    @param(CONSTANT) value : the log level according to syslog
       CRITICAL
       ERROR
       WARNING
       NOTICE
       INFO
       DEBUG
    @return(boolean) : True if set success
                        False otherwise
    """
    if self._log_level == value:
      return True

    try:
      system_logger.setLevel(value)
      self._log_level = value
      system_logger.info("Changed logging level to %s", value)
      return True
    except AttributeError:
      raise ValueError("Invalid log level")
      return False

  def setLogTarget(self, target):
    """Sets the logging target
    
    target can be a file, SYSLOG, STDOUT or STDERR.
    @param(string) target : the logging target
      STDOUT
      SYSLOG
      STDERR
      file path
    @return(boolean) : True if set success
                        False otherwise Set the log target of the logging system
    """
    if self._log_target == target:
      return True

    # set a format which is simpler for console use
    formatter = logging.Formatter("%(asctime)s %(name)-24s[%(process)d]: %(levelname)-7s %(message)s")
    if target == "SYSLOG":
      # Syslog daemons already add date to the message.
      formatter = logging.Formatter("%(name)s[%(process)d]: %(levelname)s %(message)s")
      facility = logging.handlers.SysLogHandler.LOG_DAEMON
      hdlr = logging.handlers.SysLogHandler("/dev/log", facility=facility)
    elif target == "STDOUT":
      hdlr = logging.StreamHandler(sys.stdout)
    elif target == "STDERR":
      hdlr = logging.StreamHandler(sys.stderr)
    else:
      # Target should be a file
      try:
        open(target, "a").close()
        hdlr = logging.handlers.RotatingFileHandler(target)
      except IOError:
        system_logger.error("Unable to log to " + target)
        return False

    # Remove all handler
    for handler in system_logger.handlers:
      try:
        system_logger.removeHandler(handler)
      except (ValueError, KeyError): # pragma: no cover
        system_logger.warn("Unable to remove handler %s", str(type(handler)))

    hdlr.setFormatter(formatter)
    system_logger.addHandler(hdlr)

    # Sets the logging target.
    self._log_target = target
    system_logger.info("Changed logging target to %s", target)

    return True
