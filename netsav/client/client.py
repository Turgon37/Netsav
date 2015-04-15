# -*- coding: utf8 -*-

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

"""NETSAV/client module
"""

# System imports
from http.client import HTTPConnection
import logging
from threading import Thread

# Global project declarations
sys_log = logging.getLogger('netsav')


class Client(Thread):
  """Client class that make a request to check availability of an host
  """

  UNKNOWN = 2
  AVAILABLE = 1
  UNAVAILABLE = 0

  HTTP_METHODS = ['HEAD', 'GET', 'POST']

  def __init__(self, exit, active, sync=None):
    """Constructor : init client object

    @param[threading.Event] event : the event object which define
                                  this tread life state
    """
    # Main parameters
    self.address = None
    self.port = None
    # Network parameters
    #  these value are define in second
    self.interval = 60
    self.min_retry = 2
    self.max_retry = 5
    self.tcp_timeout = 5
    #  the http method as string
    self.query_method = 'HEAD'
    # define if this client is a reference for internet accessibility
    self.is_ref = False

    # Working value
    #  remaining time before next update
    self.__remaining = 0
    #  Exiting condition
    self.__event_stop = exit
    #  Life condition
    self.__event_active = active
    # A synchronised object to allow inter thread communication
    self.__sync = sync
    #  initial status for this client
    self.__state = self.UNKNOWN
    #  trigger object to use for handling event during update
    self.__trigger = None

    Thread.__init__(self, name=__name__)

  def load(self, config):
    """Load client configuration

    @param[dict] config : a dictionnary that contain address and port
                                key-value
    @return[boolean] : True if load success
                      False otherwise
    """
    # config is given by dict
    if isinstance(config, dict):
      if 'name' in config:
        self.name = config['name']
      if 'address' in config:
        self.address = config['address']
      if 'port' in config:
        self.port = config['port']
      if 'interval' in config:
        self.interval = config['interval']
      if 'min_retry' in config:
        self.min_retry = config['min_retry']
      if 'max_retry' in config:
        self.max_retry = config['max_retry']
      if 'tcp_timeout' in config:
        self.tcp_timeout = config['tcp_timeout']
      if 'query_method' in config:
        self.query_method = config['query_method']
      if 'reference' in config:
        if config['reference'] == True:
          self.setReference()
    else:
      raise Exception('Invalid configuration type')

    return True

  def check(self):
    """Check internal client configuration

    @return[boolean] True if all config parameters are correct
                    False otherwise
    """
    if self.min_retry > self.max_retry:
      sys_log.error('[' + self.getName() +
                    '] min retry is more than max_retry')
      return False
    if self.query_method not in self.HTTP_METHODS:
      sys_log.error('[' + self.getName() + '] unknown query method value %s',
                    self.query_method)
      return False
    return True

  def run(self):
    """Run the thread
    """
    # init the remaining counter
    self.resetRemaining()
    # loop until I'm in life
    while not self.__event_stop.isSet():
      # allow ref and active client to update their state
      if self.is_ref or self.__event_active.isSet():
        self.updateState(self.queryState())
      # wait for the given time second by second
      self.__event_stop.wait(self.getRemaining())

  def queryState(self):
    """Execute a request for retrieving the associated host's state

    Make an HTTP query to determine if the server is reachable or not
    @return[int] : the server status
    """
    c_retry = 0
    c_success = 0

    # Max retry is defined by config
    while c_retry < self.max_retry:
      # if the query success the try block will continue
      # if not the except block will be run
      h = HTTPConnection(self.address, self.port, timeout=self.tcp_timeout)
      try:
        # try to query
        status = h.request(self.query_method, '/')
        # parsing the result
        res = h.getresponse()
        c_success += 1
        sys_log.debug('[' + self.getName() + '] get server code : %d',
                      res.status)
        # if we have sufficient number of success
        if c_success >= self.min_retry:
          return self.AVAILABLE
      except:
        sys_log.debug('[' + self.getName() + '] unable to reach the host')
      finally:
        c_retry += 1
    # if we have reach the max retry amount
    return self.UNAVAILABLE

  def updateState(self, state):
    """Determine if the client instance's state must be updated

    Run trigger if the status have changed
    """
    current = self.getState()
    if current != state:
      self.setState(state)
      sys_log.info('[' + self.getName() + '] Changing status to ' +
                   Client.stateToString(state))
      # run the trigger event
      if self.__trigger:
        d = self.getConfigDict()
        d['previous_state'] = current
        d['previous_state_str'] = Client.stateToString(current)
        # make the message event string
        event = ('The network status of [' + d['name'] + '] at ' +
                 d['address'] + ':' + d['port'] + ' change to ' +
                 d['current_state_str'])

        # call trigger
        self.__trigger.trig(d,
                            brief='Turn to ' + d['current_state_str'],
                            msg=event,
                            tag=d['name'])
      # Call sync function if this instance is a reference
      if self.is_ref:
        if state == self.AVAILABLE:
          self.__sync.referenceUp(self)
        elif state == self.UNAVAILABLE:
          self.__sync.referenceDown(self)

  def getName(self):
    """Return the internal name of this client object

    @return(string) : the defined name of this client
    """
    if self.name:
      if self.is_ref:
        return 'R:' + self.name
      else:
        return self.name
    else:
      return __name__

  def getInterval(self):
    """Return the time interval of this client object

    @return(int) : the defined interval in seconds
    """
    return self.interval

  def getRemaining(self):
    """Return the internal remaining time of this client object

    @return(int) : the remaining time before update this client
    """
    return self.__remaining

  def setRemaining(self, remain):
    """Set the internal remaining time of this client object

    @param(int,long) : the remaining time to set
    @return(int) : the remaining time
    """
    if isinstance(remain, int) and remain >= 0:
      self.__remaining = remain
    return self.getRemaining()

  def setTrigger(self, trigger):
    """Register a trigger object in the internal set

    @param(object) : the trigger instance to use
    """
    try:
      getattr(trigger, 'trig')
      if not self.isReference():
        self.__trigger = trigger
    except AttributeError:
      self.__trigger = None
      sys_log.error('[' + self.getName() +
                    '] the given trigger does not contain trig function')

  def resetRemaining(self):
    """Set the internal remaining time to his default value

    @return(int) : the remaining time
    """
    return self.setRemaining(self.getInterval())

  def getState(self):
    """Get the client instance's state
    """
    return self.__state

  def setState(self, state):
    """Set the client instance's state

    @param(int) : the new state of the client
    @return(int) : the state time
    """
    if isinstance(state, int):
      self.__state = state
    return self.getState()

  def setReference(self):
    """Set this client as a reference for internet accessibility

    This function does nothing if the sync object is undefined
    """
    if self.__sync is None:
      sys_log.warning('[' + self.getName() +
                      '] Unable to set this client as reference')
      return
    self.is_ref = True
    self.__sync.registerReference(self)
    # disable the internal trigger, a reference host cannot trig event
    self.__trigger = None

  def isReference(self):
    """Return the reference statement

    @return(boolean) : True if this object is a reference
                    False if it is not
    """
    return self.is_ref

  def getConfigDict(self):
    """Return the config dict for this client

    @return(dict) the dict which contain all value of this client
    """
    c = dict()
    c['name'] = self.getName()
    c['address'] = self.address
    c['port'] = str(self.port)
    c['interval'] = self.interval
    c['min_retry'] = self.min_retry
    c['max_retry'] = self.max_retry
    c['tcp_timeout'] = self.tcp_timeout
    c['current_state'] = self.getState()
    c['current_state_str'] = Client.stateToString(self.getState())
    return c

  @staticmethod
  def stateToString(state):
    """Try to associate a name to a state

    @param(int) : the state to perform among these
    @return(str) : the state as it can be perform
    """
    if state == __class__.UNAVAILABLE:
      return 'UNAVAILABLE'
    elif state == __class__.AVAILABLE:
      return 'AVAILABLE'
    elif state == __class__.UNKNOWN:
      return 'UNKNOWN'
    else:
      return str(state)
