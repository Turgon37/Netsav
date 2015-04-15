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
from .trigger.base import TriggerHandler

# Global project declarations
sys_log = logging.getLogger('netsav')


class TriggerLoader:
  """A object who load all trigger defined in config file
  """

  def __init__(self):
    """Constructor : Build a server object that will open
    """
    # Config object
    self.cp = None
    # Initialize queue
    self.__queue = Queue()
    # list of trigger object for handling
    self.__l_trigger = []

  def load(self, config_parser):
    """Load this trigger object with all defined trigger

    @param[ConfigParser] : the config parser object from which
                            retrieve configuration
    @return[boolean] : True if the loading success
                      False otherwise
    """
    if not config_parser.isLoaded():
      return False

    # parse all trigger section in config file
    for trig_sect in config_parser.getTriggerSection():
      # retrieve the current trigger configuration dict
      param = config_parser.getTriggerConfigDict(trig_sect)
      trig_name = param['name']
      # check if the trigger name contains only alpha caracters
      if not param['name'].isalpha():
        sys_log.error('[TRIGGER] Trigger name "' + trig_name +
                      '" must contains only alphabetical caracters')
        continue
      # import process
      try:
        m = __import__('netsav.trigger.' + trig_name, fromlist=['Trigger'])
        t = m.Trigger()
        if not isinstance(t, TriggerHandler):
          # inheritance error
          sys_log.error('[TRIGGER] Trigger "' + trig_name +
                        '" must inherit from TriggerHandler class')
          continue
        t.setLogger(sys_log)
        if t.load(param):
          self.__l_trigger.append(t)
          sys_log.debug('[TRIGGER] Loaded trigger ' + trig_name)
        else:
          # loading error
          sys_log.error('[TRIGGER] Trigger "' + trig_name +
                        '" cannot be load')
      except ImportError as e:
        sys_log.error('[TRIGGER] Trigger "' + trig_name +
                      '" name cannot be found in trigger directory' + str(e))
      except NotImplementedError as e:
        sys_log.error('[TRIGGER] Trigger "' + trig_name +
                      '" must implement the method "' + str(e) + '"')
      except KeyError as e:
        sys_log.error('[TRIGGER] Trigger "' + trig_name + '" require ' +
                      str(e) +
                      ' missing parameters see trigger documentation')
      except Exception as e:
        sys_log.error('[TRIGGER] Trigger "' + trig_name +
                      '" has encounter an unknown error: ' + str(e))

    # return false if no trigger have been loaded
    return self.hasTrigger()

  def hasTrigger(self):
    """Check if there is/are registered trigger

    @return[boolean] : True if th trigger handler contains at least one trigger
                       False otherwise
    """
    return len(self.__l_trigger) > 0

  def trig(self,
           value=None,
           msg='No message',
           brief='No brief',
           tag='NETSAV'):
    """Receive a trig event from client and stack it on queue

    @param(dict) value : a set of value to pass to the trigger
    @param(string) msg : a string which describe the event
    @param(string) brief : a brief string which fill the subject
    @param(string) tag : a tag to put in front of notification
    @return(boolean) : True if event successfully queued
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

    sys_log.debug('[TRIGGER] Event queued for client [' +
                  value['name'] + ']')
    self.__queue.put(value)
    return True

  def serve_once(self):
    """Handle only one event from the queue if available

    @return[boolean] : True if a trigger has been serve
                        False there is no trigger in queue
    """
    if self.__queue.empty():
      return False
    value = self.__queue.get_nowait()
    sys_log.info('[TRIGGER] Trigger for client [' +
                 value['name'] + ']')
    self.__do(value)
    return True

  def serve(self):
    """Handle all event from the queue undefinitly
    """
    while True:
      value = self.__queue.get(True)
      sys_log.info('[TRIGGER] Trigger for client [' +
                   value['name'] + ']')
      self.__do(value)

  def __do(self, value):
    """Send a trig event to all registered trigger objects

    @param(dict) value : a set of value to pass to all trigger
    """
    if value is None:
      return
    for t in self.__l_trigger:
      try:
        if not t.do(value):
          sys_log.error('[TRIGGER] Trigger "' + t.getName() +
                        '" has encounter an error during do()')
      except KeyError as e:
        sys_log.error('[TRIGGER] Trigger "' + t.getName() +
                      '" require a missing parameters "' + str(e) +
                      '" see trigger documentation')
      except Exception as e:
        sys_log.error('[TRIGGER] Trigger "' + t.getName() +
                      '" has encounter an error: ' + str(e))
