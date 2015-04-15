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

"""NETSAV/sync module
"""

# System imports
import logging
import logging.handlers
import threading

# Projet Imports

# Global project declarations
sys_log = logging.getLogger('netsav')


class Sync:
  """This class provide a synchronised object that provide a communicate bus between all thread
  """
  def __init__(self, active):
    """Constructor : init sync object

    @param[threading.Event] event : the event object that can disable all non-ref client
    """
    self._active = active
    # define lock to avoid conflict access
    self._lock_register = threading.Lock()
    self._lock_counter = threading.Lock()
    # define the number of reference
    self._counter_ref = 0
    # define the number of reference which is/are down
    self._counter_ref_down = 0
    # reference name list
    self._d_ref = dict()

  def registerReference(self, ref):
    """Register a reference name and increase the reference counter
    """
    name = ref.getName()
    # block other thread
    self._lock_register.acquire()
    if name not in self._d_ref:
      self._d_ref[name] = ref.getState()
      self._counter_ref += 1
    else:
      sys_log.error('Reference "'+name+'" already registrered')
    # free the register
    self._lock_register.release()

  def referenceUp(self, ref):
    """Call when a reference change to up state
    
    @param[Client] ref : the client reference object 
    """
    self._lock_counter.acquire()
    name = ref.getName()
    # if reference is registered
    if name in self._d_ref:
      # if old state was down
      if self._d_ref[name] in [ref.UNAVAILABLE, ref.UNKNOWN]:
        # update state
        self._d_ref[name] == ref.getState()
        self.decreaseDownCounter()
        sys_log.info('['+name+'] Reference is up')
    self._lock_counter.release()

  def referenceDown(self, ref):
    """Call when a reference change to down state
    
    @param[Client] ref : the client reference object 
    """
    self._lock_counter.acquire()
    name = ref.getName()
    # if reference is registered
    if name in self._d_ref:
      # if old state was down
      if self._d_ref[name] in [ref.AVAILABLE, ref.UNKNOWN]:
        # update state
        self._d_ref[name] == ref.getState()
        self.increaseDownCounter()
        sys_log.info('['+name+'] Reference is down')
    self._lock_counter.release()

  def increaseDownCounter(self):
    """Increase the internal down reference counter
    
    This function manage the counter for increase operations
    It update the client active state according to this counter
    """
    if self._counter_ref_down == self._counter_ref:
      return False
    self._counter_ref_down += 1
    self.refreshActiveState()
    return True

  def decreaseDownCounter(self):
    """Decrease the internal up reference counter
    
    This function manage the counter for decrease operations
    It update the client active state according to this counter
    """
    if self._counter_ref_down <= 0:
      return False
    self._counter_ref_down -= 1
    # if there is at least one ref down
    self.refreshActiveState()
    return True

  def refreshActiveState(self):
    """Update the non-ref active client status according to down ref counter
    """
    if self._counter_ref_down == 0:
      # enable all simple client
      self._active.set()
      sys_log.debug('[SYNC] Enable all non-ref client')
    else:
      # disable all simple client
      self._active.clear()
      sys_log.debug('[SYNC] Disable all non-ref client')