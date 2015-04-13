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
import gc
import logging
from threading import Thread
import time

# Global project declarations
system_logger = logging.getLogger('netsav')

class Client(Thread):
  """Client class that make a request to check availability of an host
  """
  
  UNKNOWN = 2
  AVAILABLE = 1
  UNAVAILABLE = 0
  
  HTTP_METHODS = ['HEAD', 'GET', 'POST']
  
  def __init__(self, name = None, address = None, port = None, interval = None,
                  conf_dict = None, trigger = None):
    """Constructor : init client object with network parameters

    @param(string) name : the instance name
    @param(string) address : the address of the server socket
    @param(int) port : port number
    @param(int) interval : the number of second between two query to the client
    @param(dict) conf_dict : a dictionnary that contain address and port key-value
    @param(netsav.Trigger) trigger : the trigger object on which call 
    """
    # Self config of this client
    # Main parameters
    def_name = __name__
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
    
    # Working value
    #  remaining time before next update
    self._remaining = 0
    #  looping value
    self._continue = True
    #  initial status for this client
    self._state = self.UNKNOWN
    #  trigger object to use for handling event during update
    self._trigger = None

    # config is given by dict
    if isinstance(conf_dict, dict):
      if 'name' in conf_dict:
        def_name = conf_dict['name']
      if 'address' in conf_dict:
        self.address = conf_dict['address']
      if 'port' in conf_dict:
        self.port = conf_dict['port']
      if 'interval' in conf_dict:
        self.interval = conf_dict['interval']

      # Optionnal parameters
      if 'min_retry' in conf_dict:
        self.min_retry = conf_dict['min_retry']
      if 'max_retry' in conf_dict:
        self.max_retry = conf_dict['max_retry']
      if 'tcp_timeout' in conf_dict:
        self.tcp_timeout = conf_dict['tcp_timeout']
      if 'query_method' in conf_dict:
        self.query_method = conf_dict['query_method']

    if name:
      def_name = name

    if address and port:
      self.address = address
      self.port = port

    if interval:
      self.interval = interval
    
    Thread.__init__(self, name = def_name)  
    if trigger:
      self.setTrigger(trigger)
    system_logger.debug('['+self.getName()+"] run with conf = %s", conf_dict)

  def run(self):
    """Run the query thread
    """
    self.resetRemaining()  
    while self._continue:
      self.updateState(self.queryState())
      for i in range(self.getRemaining()):
        if self._continue == True:
          time.sleep(1)
      
  def exit(self):
    """Run the query thread
    """
    self._continue = False

  def queryState(self):
    """Execute a request for retrieving the associated host's state

    Make an HTTP query to determine if the server is reachable or not
    @return(int) : the server status
    """
    c_retry = 0
    c_success = 0

    # Max retry is defined by config
    while c_retry < self.max_retry:
      # if the query success the try block will continue
      # if not the except block will be run
      h = HTTPConnection(self.address, self.port, timeout = self.tcp_timeout)
      try:
        # try to query
        status = h.request(self.query_method, '/')
        # parsing the result
        res = h.getresponse()
        c_success += 1
        system_logger.debug('['+self.getName()+'] get server code : %d',
                                                    res.status)
        # if we have sufficient number of success
        if c_success >= self.min_retry:
          return self.AVAILABLE
      except:
        system_logger.debug('['+self.getName()+'] unable to reach the host')
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
      system_logger.info('['+self.getName()
              +'] Changing status to '+Client.performStateString(state))
      # run the trigger event
      if self._trigger:
        d = self.getConfigDict()
        d['previous_state'] = current
        d['previous_state_str'] = Client.performStateString(current)
        # make the message event string
        event = (
          'The network status of ['+
          d['name']+'] at '+d['address']+':'+d['port']+
          ' change to '+d['current_state_str']
          )
        # call trigger
        self._trigger.trig(d, 
            brief = 'Turn to '+d['current_state_str'],
            msg = event,
            tag = d['name'])

  def check(self):
    """Check internal client configuration
    
    @return(boolean) True if all config parameters are correct
                    False otherwise
    """
    if self.min_retry >= self.max_retry:
      system_logger.error('['+self.getName()
          +'] min retry is more than max_retry')
      return False
    if self.query_method not in self.HTTP_METHODS:
      system_logger.error('['+self.getName()
          +'] unknown query method value %s', self.query_method)
      return False
    return True

  def getName(self):
    """Return the internal name of this client object
    
    @return(string) : the defined name of this client
    """
    if self.name:
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
    return self._remaining

  def setRemaining(self, remain):
    """Set the internal remaining time of this client object
    
    @param(int,long) : the remaining time to set
    @return(int) : the remaining time
    """
    if isinstance(remain, int) and remain >= 0:
      self._remaining = remain
    return self.getRemaining()
    
  def setTrigger(self, trigger):
    """Register a trigger object in the internal set
    
    @param(object) : the trigger instance to use
    """
    try:
      getattr(trigger, 'trig')
      self._trigger = trigger
    except AttributeError:
      self._trigger = None
      system_logger.error('['+self.getName()
          +'] the given trigger does not contain trig function')

  def resetRemaining(self):
    """Set the internal remaining time to his default value
    
    @return(int) : the remaining time
    """
    return self.setRemaining(self.getInterval())

  def getState(self):
    """Get the client instance's state
    """
    return self._state

  def setState(self, state):
    """Set the client instance's state
    
    @param(int) : the new state of the client
    @return(int) : the state time
    """
    if isinstance(state, int):
      self._state = state
    return self.getState()
    
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
    c['current_state_str'] = Client.performStateString(self.getState())
    return c
    
  def performStateString(state):
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