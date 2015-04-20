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

# Projet Imports


class TriggerHandler:
  """Abstract class that must be the parent of all trigger handler class

  All trigger are executed consecutively by the main thread who is different
  from client(s) and server thread

  The constructor must initialise some needed attribut but didn't receive any
  parameter
  The getter getName() is an accessor for netsav module during event handling
  The setter setLogger(logger) is an accessor for netsav module, it provide a
  door to put a logger object. It permit your trigger to put some log into the
  main logger system
  
  The function load(config) is use by main module to load the configuration into the
  """

  def __init__(self):
    """Constructor : Build a specific trigger
    """
    self._config = None
    self._logger = None

  def getName(self):
    """Return the name (type) of this trigger

    This is an accessor for netsav module
    @return[string] the name of this trigger
    """
    if self._config:
      if 'name' in self._config:
        return self._config['name']
    return 'unknown'

  def setLogger(self, logger):
    """Use to set a internal logger for this trigger

    This is an accessor for netsav module
    @param[logging object] logger : the logger object to use
    """
    self._logger = logger

  def setConfiguration(self, config):
    """Use to setup the internal configuration dict by the netsav module

    This is an accessor for netsav module
    @param[dict] config : the dict which contains the key value parameters
    """
    self._config = config

  def load(self, config):
    """(To overload)Function that must load this trigger object

    API for netsav module
    The return value of this function determine if the trigger must
    be loaded or not. If this return false, the trigger will not be use
    @return[boolean] :  True if load success
                        False otherwise
    """
    raise NotImplementedError('load()')

  def do(self, value=None):
    """(To overload)The called function when an event must be trigged by this

    API for netsav module
    The return value of this function will be looked and some log will be
    generated if the result is False
    This function is called each time an event happen. All event contain
    a set of information about what happen in a python dict. They are available
    by these key :
    'name', 'address', 'port', 'interval', 'min_retry',
     'max_retry', 'tcp_timeout', 'current_state', 'current_state_str',
     'previous_state', 'previous_state_str', 'msg', 'brief', 'tag'
    @param[dict] value : the dict which contains the key value refer to this
                          event
    @return[boolean] :  True if execution success
                        False otherwise
    """
    raise NotImplementedError('do(value)')
