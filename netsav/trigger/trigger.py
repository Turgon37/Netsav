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

# System imports
import logging
from queue import Queue

# Projet Imports


# Global project declarations
system_logger = logging.getLogger('netsav')

class TriggerLoader:
  """A object who load all trigger defined in config file
  """
  
  def __init__(self, name = None, configparser = None):
    """Constructor : Build a server object that will open
    
    @param(netsav.configparser) configparser :
        The configparser object to use for get all parameter from config file
    """
    # Config object
    self._configparser = None
    # Initialize queue
    self._queue = Queue()
    # name used to identify specific trigger
    self._name = __name__
    
    if name:
      self._name = name
    if configparser:
      self._configparser = configparser
    self._l_trigger = []
      
  def load(self):
    """Load this trigger object with all defined trigger
    
    @return(boolean) : True if the loading success
                      False otherwise
    """
    if not self._configparser.isLoaded():
      return False
      
    # parse all trigger section in config file
    for trig_sect in self._configparser.getTriggerSection():
      # retrieve the current trigger configuration dict
      param = self._configparser.getTriggerConfigDict(trig_sect)
      trig_name = param['name']
      # check if the trigger name contains only alpha caracters
      if not param['name'].isalpha():
        system_logger.error('['+self._name+'] Trigger "'+trig_name+
                '" must contains only alphabetical caracters')
        continue
      # import process
      try:
        m = __import__('netsav.trigger.'+trig_name, fromlist = ['Trigger'])
        #import netsav.trigger.mail as m
        t = m.Trigger()
        if not isinstance(t, TriggerHandler):
          # inheritance error
          system_logger.error('['+self._name+'] Trigger "'+trig_name+
                      '" does not inherit from TriggerHandler ')
          continue
        t.setLogger(system_logger)
        if t.load(config = param):
          self._l_trigger.append(t)
          system_logger.debug('['+self._name+'] Loaded '+trig_name)
        else:
          # loading error
          system_logger.error('['+self._name+'] Trigger "'+trig_name+
                      '" cannot be load')
      except ImportError:        
        system_logger.error('['+self._name+'] Trigger "'+trig_name+
                  '" name cannot be found in trigger directory')
      except NotImplementedError as e:
        system_logger.error('['+self._name+'] Trigger "'+trig_name+
                    '" must implement the method "'+str(e)+'"')
      except KeyError as e:
        system_logger.error('['+self._name+'] Trigger "'+trig_name+
                    '" require '+str(e)+' missing parameters see trigger '+
                    'documentation')
      except Exception as e:
        system_logger.error('['+self._name+'] Trigger "'+trig_name+
                    '" has encounter an error: '+str(e))

    # return false if no trigger have been loaded
    return self.hasTrigger()

  def hasTrigger(self):
    """Check if there is/are registered trigger
    
    @return(boolean) : True if this contains at least one trigger
                       False otherwise
    """
    if len(self._l_trigger) > 0:
      return True
    else:
      return False

  def trig(self, value = None, 
                  msg = 'unknown', 
                  brief = 'unknown',
                  tag = 'unknown'):
    """Receive a trig event from client and stack it on queue
    
    @param(dict) value : a set of value to pass to the trigger
    @param(string) msg : a string which describe the event
    @param(string) brief : a brief string which fill the subject
    @param(string) tag : a tag to put in front of notification
    @return(boolean) : True if trig action success
                       False otherwise
    """
    if not self.hasTrigger():
      return False

    if not isinstance(value, dict):
      value = dict(value)

    if 'name' not in value:
      value['name'] = 'unknown'
    if 'msg' not in value:
      value['msg'] = msg
    if 'brief' not in value:
      value['brief'] = brief
    if 'tag' not in value:
      value['tag'] = tag

    system_logger.debug('['+self._name+'] Trigger queued for client ['
      +value['name']+']')
    self._queue.put_nowait(value)
    return True
    
  def serve(self):
    """Trigger serve call trig an event from the queue if exist
    
    @return(boolean) : True if a trigger has been serve
                        False there is no trigger in queue
    """
    if self._queue.empty():
      return False
    value = self._queue.get_nowait()
    system_logger.info('['+self._name+'] Trigger for client ['
      +value['name']+']')
    self.trigAll(value)
    return True
    
  def trigAll(self, value):
    """Send a trig event to all registered trigger objects
    
    @param(dict) value : a set of value to pass to all trigger
    """
    if value is None:
      return
    for t in self._l_trigger:
      try:
        t.do(value)
      except KeyError as e:
        system_logger.error('['+self._name+'] Trigger "'+t.getName()+
                    '" require a missing parameters "'+str(e)+
                    '" see trigger documentation')
      except Exception as e:
        system_logger.error('['+self._name+'] Trigger "'+t.getName()+
                    '" has encounter an error: '+str(e))

class TriggerHandler:
  """Abstract class must be a base of an trigger handler class
  """
  
  # value considered as True in the config file
  BOOL_TRUE_MAP = ['true', 'TRUE', 'True', '1']
  
  def __init__(self):
    """Constructor : Build a specific trigger
    """
    self._config = None
    self._logger = None
  
  def getName(self):
    """Return the name (type) of this trigger
    
    @return(string) the name of this trigger
    """
    if self._config:
      if 'name' in self._config:
        return self._config['name']
    return 'unknown'
  
  def setLogger(self, logger = None):
    """Use to set a internal logger for this trigger
    
    @param(logging object) logger : the logger object to use
    """
    if logger:
      self._logger = logger
    
  def load(self, config = None):
    """(To overload)Function that load this trigger configuration 'config' dict
    
    @param(dict) config :the dict which contains the key value parameters
    @return(boolean) :  True if load success
                        False otherwise
    """
    raise NotImplementedError('load')

  def do(self, value = None):
    """(To overload)The called function when an event must be trigged by this
    
    @param(dict) value : the dict which contains the key value refer to this
                          event
    """
    raise NotImplementedError('do')