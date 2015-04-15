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

  def setLogger(self, logger):
    """Use to set a internal logger for this trigger

    @param[logging object] logger : the logger object to use
    """
    if logger:
      self._logger = logger

  def load(self, config):
    """(To overload)Function that load this trigger configuration 'config' dict

    @param[dict] config :the dict which contains the key value parameters
    @return[boolean] :  True if load success
                        False otherwise
    """
    self._config = config

  def do(self, value=None):
    """(To overload)The called function when an event must be trigged by this

    @param(dict) value : the dict which contains the key value refer to this
                          event
    """
    raise NotImplementedError('do')
