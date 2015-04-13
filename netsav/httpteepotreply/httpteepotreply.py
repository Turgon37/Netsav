# -*-coding:Utf-8 -*

# This file is a part of HttpTeepotReply
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

"""Main HttpTeepotReply module, contains main Class

If you use self.server_forever() the server will handle indefinitly client request
Else is you use self.handle_request() the server will handle request until timeout (defined by self.timeout=X) is reached, then it will run the handle_timeout and return
"""

# System imports
import logging
import logging.handlers
import os
import re
import socket
import sys

# Projet Imports
from http.server import HTTPServer, BaseHTTPRequestHandler

class HttpTeepotReply(HTTPServer):
  """(extend HTTPServer) Run a simple http server
  
  Http light Server class
  Open a listening socket on specified address and port
  address => 'the iface on which listen'
  port => 'the port on which listen'
  """
  
  IPV4_REGEX = '^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$'
  DN_REGEX = '^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$'
  
  def __init__(self, address = '0.0.0.0', port = None, logger = None, 
                              bind_and_activate = True,
                              log_client = True):
    """Constructor : Build an http teepot reply server
    
    @param(string) address : the address on which the server socket will listen
    @param(int) port : port listening number
    @param(logging.logger) logger : an optional logger object in which the 
                                    server will send log
    @param(boolean) bind_and_activate : define bind_and_activate option see 
                                          socketserver.TCPServer
    @param(boolean) log_client : print a log entry for each client who make a query to this server
    """
    # Get logger
    if logger is None:
      self._logger = self._loggerInit()
    else:
      self._logger = logger
    self._if_log_client = log_client
    # Get port
    if port:
      try:
        self._port = int(port)
      except ValueError:
        self._logger.error("Port number is not a valid int : '%s'", port)
        sys.exit(-1)
    else:
      self._logger.error('Port number is not given')
      sys.exit(-1)
    # Get address
    if address:
      if re.match(self.IPV4_REGEX, address) is None or re.match(self.DN_REGEX, address) is None:
        self._logger.error("Incorrect bind address read in configuration file:"
                            +" '%s'",
                            address)
        self._logger.error("Address string is invalid : '%s'", address)
        sys.exit(-1)
      else:
        self._address = address
    else:
      self._logger.error('Address string is not given')
      sys.exit(-1)
    # init handling object
    self._h_class = None
    self._h_func = None
    self._h_obj = None

    HTTPServer.__init__(self, (self._address, self._port),
                        HttpReplyHandler,
                        bind_and_activate)

  def serve_forever(self):
    """Handle incoming request forever
    """
    if not( self._address and self._port):
      self._logger.error('Invalid network configuration')
      return False

    self._logger.info('Starting HTTP server on '
                        +str(self._address)
                        +':'
                        +str(self._port))
    try:
      HTTPServer.serve_forever(self)
    except (KeyboardInterrupt, SystemExit):
      self._logger.error('## Abnormal termination ##')
    
  def handle_timeout(self):
    """Special handler for periodic event defined by setTimeoutHandler
    
    This override the handle_timeout function in HTTPServer
    It run a specific function defined by setTimeoutHandler
    """
    if self._h_obj and self._h_func:
      f = getattr(self._h_obj, self._h_func, None)
      if f:
        f()
      else:
        self._logger.error('Unable to execute the timeout handling method')
    elif self._h_class and self._h_func:
      # TODO 3.
      #obj = self._h_class()
      #obj._h_func()
      pass
    
  def setTimeoutHandler(self, h_class, h_func, h_obj = None):
    """Define the func in class to call when the timeout expire
    
    @param(string) h_class : the name of the class who contain h_func
    @param(string) h_func : the name of the function to run
    @param(Obj) h_obj : an instance of the h_class on which run the h_func 
                        directly
                        
    If h_obj is given the timeout handler will call h_func on this obj directly
    Else it make a new instance of h_class
    """
    self._h_class = h_class
    self._h_func = h_func
    if h_obj:
      self._h_obj = h_obj

  def _loggerInit(self):
    """Return a minimal logger object
    
    Logging is set to STDOUT
    @return(logging.logger) : the created logger
    """
    logger = logging.getLogger(__name__)

    formatter = logging.Formatter("%(asctime)s %(name)-24s[%(process)d]: %(levelname)-7s %(message)s")
    hdlr = logging.StreamHandler(sys.stdout)
    hdlr.setFormatter(formatter)

    logger.addHandler(hdlr)
    logger.setLevel('INFO')

    return logger



class HttpReplyHandler(BaseHTTPRequestHandler):
  """Http request reply handler class
  
  Define an extension of the BaseHTTPRequestHandler to handle client queries
  """

  def do_HEAD(self):
    """Implement handler to HEAD request
    """
    self.do_GET()

  def do_GET(self):
    """Implement handler to GET request
    """
    self.send_response_only(418, 'I\'m a teepot')
    self.send_header('Content-type', 'text/plain')
    self.send_header('Date', self.date_time_string())
    self.end_headers()
    self._log_client()

  def do_POST(self):
    """Implement handler to POST request
    """
    self.do_GET()

  def _log_client(self):
    """Emit logs messages to keep trace of incoming client request
    """
    if self.server._if_log_client:
      self.server._logger.info('Receive a %s query from host %s:%s', 
                              self.command,
                              self.client_address[0],
                              self.client_address[1])



def main():
  """Simple main for running a instance of the http server"""
  try:
    if sys.argv[1:]:
      port = int(sys.argv[1])
    else:
      port = None
  except ValueError:
    print("Port number is invalid : '"+str(sys.argv[1])+"'")
    sys.exit(-1)

  httpd = HttpTeepotReply(port = port)
  try:
    httpd.serve_forever()
  except (KeyboardInterrupt, SystemExit):
    sys.exit(0)

##
# Run launcher as the main program
if __name__ == '__main__':
  main()
