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

"""NETSAV program

A network system availability checker for remote host
(as example two server over Internet)
https://github.com/Turgon37/netsav
"""

# System imports
import logging
import logging.handlers
import os
import signal
import socket
import sys
import threading
import time

# Projet Imports
from .config import NetsavConfigParser
from .sync import Sync
from .triggerloader import TriggerLoader
from .server.server import Server
from .client.client import Client

# Global project declarations
sys_log = logging.getLogger('netsav')


class Netsav:
  """Build a program object, run a server and several clientconfiguration file

  Configuration are read from the config file given to the constructor
  run a client thread for each client section of the configuration file
  """

  def __init__(self, daemon=False, log_level='INFO'):
    """Constructor : Build the program lead object

    @param[string] config : configuration file's path
    @param[boolean] daemon : if the server must be daemonized (False)
    @param[string] log_level : the system minimum logging level for put log
                                message
    """
    # config parser
    self.cp = NetsavConfigParser()

    self.is_daemon = daemon
    # Local entities
    #  server obj
    self.__server = None
    #  client thread list
    self.__l_client = []
    # log parameters
    self.__log_level = None
    self.__log_target = None
    # global trigger object to use for client notify
    self.__trigger = None
    # A synchronous event for thread exiting
    self.__event_stop = threading.Event()
    self.__event_stop.clear()
    # A synchronous event for threading activating
    self.__event_active = threading.Event()
    self.__event_active.set()
    # New lock instance
    self.__sync = Sync(self.__event_active)

  def load(self, config):
    """Loading function

    Use this function to load the configuration file
    @param[string] config : The path fo the configuration file
    @return[boolean] : True if success
                        False otherwise
    """
    if config is not None:
      if self.cp.load(config):
        self.setLogLevel(self.cp.getOptLogLevel())
        self.setLogTarget(self.cp.getOptLogTarget())
        return True
    return False

  def start(self, pid_path):
    """Run the service

    Daemonize if daemon is True in constructor
    @param[string] pid_path : pid file's path
    @return[boolean] : True is start success
                      False otherwise
    """
    # Restreint access to only owner
    os.umask(0x0077)

    # Installing signal catching function
    signal.signal(signal.SIGTERM, self.__sigTERMhandler)
    signal.signal(signal.SIGINT, self.__sigTERMhandler)

    # Load configuration
    if not self.cp.isLoaded():
      return False

    is_ignore_own = self.cp.getOptIgnoreOwn()

    # Turn in daemon mode
    if self.is_daemon:
      sys_log.debug('Starting in daemon mode')
      if self.__daemonize():
        sys_log.info('Daemon started')
      else:
        sys_log.error('Could not create daemon')
        raise Exception('Could not create daemon')

    # Create the pid file
    try:
      sys_log.debug("Creating PID file %s", pid_path)
      pid_file = open(pid_path, 'w')
      pid_file.write(str(os.getpid()) + '\n')
      pid_file.close()
    except IOError as e:
      sys_log.error("Unable to create PID file: %s", pid_path)

    # Init clients objects
    client_list = self.cp.getClientConfigDict()
    for name in client_list:
      # Ignore self hostname declaration
      if is_ignore_own is True and name == socket.gethostname():
        sys_log.debug("Ignoring client %s", name)
      else:
        cli = Client(self.__event_stop, self.__event_active, self.__sync)
        if cli.load(client_list[name]) and cli.check():
          cli.setTrigger(self.getTrigger())
          self.__l_client.append(cli)
          sys_log.info("Added client : %s", name)
        else:
          sys_log.error("Failed to add client : %s", name)

    # Init server object
    self.__server = Server(self.__event_stop)
    if self.__server.load(self.cp.getServerConfigDict()) and self.__server.open():
      # Run the main loop
      self.__downgrade()
      self.run()
    else:
      sys_log.error('Error during server opening')

    # Stop threads
    self.stop()

    # Remove the pid file
    try:
      sys_log.debug("Remove PID file %s", pid_path)
      os.remove(pid_path)
    except OSError as e:
      sys_log.error("Unable to remove PID file: %s", e)

    sys_log.info("Exiting netsav")
    return True

  def run(self):
    """Main loop function

    This function is saperated from the start() for old Thread implement needed
    It only provide the main service loop and It is launch by start()
    """
    try:
      sys_log.debug("Starting server thread")
      self.__server.start()

      if self.hasClient():
        sys_log.debug("Starting all client thread")
        for c in self.__l_client:
          c.start()
        # serve all trigger
        sys_log.debug("Waiting on trigger serve")
        self.getTrigger().serve()
      else:
        sys_log.debug("Waiting on server thread")
        # wait for server terminate
        self.__server.join()
    except SystemExit:
      return
    except KeyboardInterrupt:
      sys_log.error('## Abnormal termination ##')

  def stop(self):
    """ Stop properly the server after signal received

    It is call by start() et signalHandling functions
    It says to all threadto exit themself
    """
    # Tell to all thread to stop them at the next second
    sys_log.debug('Send exit command to all thread')
    # send stop command via synchronised event
    self.__event_stop.set()

    # ensure that all of them have exit, and add eventual event to trig queue
    sys_log.debug('Waiting for all subthread exiting')
    while (threading.enumerate().__len__()) > 1:
      self.getTrigger().serve_once()
      time.sleep(0.5)

    # serve all event which have not already been serve
    sys_log.debug('Purge and serve all event in the queue')
    while (self.getTrigger().serve_once()):
      pass

    # Close log
    logging.shutdown()

  #
  # System running functions
  #

  def __sigTERMhandler(self, signum, frame):
    """Make the program terminate after receving system signal
    """
    sys_log.debug("Caught system signal %d", signum)
    sys.exit(1)

  def __downgrade(self):
    """Downgrade netsav privilege to another uid/gid
    """
    uid = self.cp.getOptUid()
    gid = self.cp.getOptGid()

    try:
      if gid is not None:
        sys_log.debug("Setting process group to gid %d", gid)
        os.setgid(gid)
      if uid is not None:
        sys_log.debug("Setting process user to uid %d", uid)
        os.setuid(uid)
    except PermissionError:
      sys_log.error('Insufficient privileges to set process id')

  def __daemonize(self):
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

    if (pid == 0):  # The first child.
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
      os._exit(0)  # Exit parent of the first child.
    return True

  #
  # Client managment functions
  #
  def hasClient(self):
    """Check if there is/are registered clients

    @return(boolean) : True if list contains at least one client
                       False otherwise
    """
    if len(self.__l_client) > 0:
      return True
    else:
      return False

  #
  # Trigger
  #
  def getTrigger(self):
    """Return the instance of the trigger object

    @return(netsav.Trigger) if config is being loaded
                None otherwise
    """
    if not self.cp.isLoaded():
      return None
    if self.__trigger is None:
      t = TriggerLoader()
      if not t.load(self.cp):
        sys_log.warning('No trigger loaded, all client event will be drop')
      self.__trigger = t
    return self.__trigger

  #
  # Logging functions
  #
  def setLogLevel(self, value):
    """Set the logging level.

    @param(CONSTANT) value : the log level according to syslog
       CRITICAL
       ERROR
       WARNING
       NOTICE
       INFO
       DEBUG
    @return[boolean] : True if set success
                        False otherwise
    """
    if self.__log_level == value:
      return True

    try:
      sys_log.setLevel(value)
      self.__log_level = value
      sys_log.info("Changed logging level to %s", value)
      return True
    except AttributeError:
      raise ValueError("Invalid log level")

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
    if self.__log_target == target:
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
        sys_log.error("Unable to log to " + target)
        return False

    # Remove all handler
    for handler in sys_log.handlers:
      try:
        sys_log.removeHandler(handler)
      except (ValueError, KeyError):
        sys_log.warn("Unable to remove handler %s", str(type(handler)))

    hdlr.setFormatter(formatter)
    sys_log.addHandler(hdlr)
    # Sets the logging target.
    self.__log_target = target
    sys_log.info("Changed logging target to %s", target)
    return True
