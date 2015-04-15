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
from socket import error as Error
from threading import Thread

# Projet Imports
from ..httpteepotreply.httpteepotreply import HttpTeepotReply

# Global project declarations
sys_log = logging.getLogger('netsav')

class Server(Thread):
  """Simple HTTP Server class that make light answer to http queries
  """

  def __init__(self, event):
    """Constructor : Build a server object that will open
    
    @param[threading.Event] event : the event object which define this tread life state
    """
    # a synchronised event that indicates the continuity of the thread
    self.__event_stop = event

    self.address = None
    self.port = None
    self.log_client = True

    # Server instance
    self.http = None
    Thread.__init__(self, name = 'HTTP_SERVER')

  def load(self, config):
    """
    @param[dict] config : a dictionnary that contain address and port 
                                key-value
    @return[boolean] : True if load success
                      False otherwise
    """
    if isinstance(config, dict):
      self.address = config['address']
      self.port = config['port']
      if 'log_client' in config:
        self.log_client = config['log_client']
    else:
      raise Exception('Invalid configuration type')
      return False
    self.http = HttpTeepotReply(self.address,
                                self.port,
                                sys_log,
                                bind_and_activate = False,
                                log_client = self.log_client)
    return True

  def open(self):
    """Bind network socket
    
    @return[boolean] : True if bind success
                        False otherwise
    """
    if not (self.address and self.port):
      sys_log.error('Invalid server network configuration')
      return False

    # Open socket separatly for checking bind permissions
    try:
      self.http.server_bind()
      self.http.server_activate()
    except Error:
      sys_log.error("Unable to open socket on port %s", self.port)
      return False

    # Run the server
    sys_log.debug("Opening local server socket on %s:%s",
                        self.address,
                        self.port)
    return True
    
  def close(self):
    """Close network socket
    """
    try:
      self.getServerInstance().socket.close()
      sys_log.debug('Closing local server socket')
    except Error:
      sys_log.error('Unable to close server socket')

  def getServerInstance(self):
    """Return the HTTP server instance
    """
    return self.http

  def run(self):
    """Run the thread
    """
    http = self.getServerInstance()
    while not self.__event_stop.isSet():
      http.timeout = 0.5
      http.handle_request()
      self.__event_stop.wait(0.5)

    # close the socket
    self.close()