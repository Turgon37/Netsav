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

# Projet Imports
from httpteepotreply.httpteepotreply import HttpTeepotReply

# Global project declarations
system_logger = logging.getLogger('netsav')

class Server:
  """Simple HTTP Server class that make light answer to http queries
  """
  
  def __init__(self, address = None, port = None, conf_dict = None):
    """Constructor : Build a server object that will open
    
    @param(string) address : the address of the server socket
    @param(int) port : port number
    @param(dict) config_dict : a dictionnary that contain address and port 
                                key-value
    """
    # address and port are not None
    log_client = True
    
    if address and port:
      self._address = address
      self._port = port
    elif isinstance(conf_dict, dict):
      self._address = conf_dict['address']
      self._port = conf_dict['port']
      if 'log_client' in conf_dict:
        log_client = conf_dict['log_client']
    else:
      raise Exception('address and port are not valid')

    # Build an server instance
    self._http_server = HttpTeepotReply(self._address,
                                      self._port, system_logger, 
                                      bind_and_activate = False,
                                      log_client = log_client)

  
  def start(self):
    """ Start the server instance, open socket and bind network
    
    """
    if not (self._address and self._port):
      system_logger.error("Invalid server network configuration")
      return False

    # Open socket separatly for checking bind permissions
    system_logger.debug('Opening local socket')
    try:
      self._http_server.server_bind()
      self._http_server.server_activate()
    except Error:
      system_logger.error("Unable to open socket on port %s", self._port)
      return False

    # Run the server
    system_logger.debug('Starting server instance with %s:%s', 
                        self._address,
                        self._port)
    return True
    
  def getServerInstance(self):
    """Return the HTTP server instance
    """
    return self._http_server
