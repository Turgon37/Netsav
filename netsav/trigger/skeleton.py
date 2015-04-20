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
# Put here your system needed imports


# Projet Imports
from .base import TriggerHandler


class Trigger(TriggerHandler):
  """A simple trigger skeleton

  You can use it as base for build your own trigger class
  """

  def __init__(self):
    """(override)Default constructor:

    !! Keep the call to parent constructor
    Put here some attribut initialisation
    """
    TriggerHandler.__init__(self)

  def load(self):
    """Load configuration from conf file

    The return value of this function determine if the trigger must
    be loaded or not. If this return false, the trigger will not be use
    @return[boolean] :  True if load success
                        False otherwise
    """
    return True

  def do(self, value):
    """This function must implement the execution of your trigger

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
    return True
