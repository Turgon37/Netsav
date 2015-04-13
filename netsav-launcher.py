#!/usr/bin/python3
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

"""NETSAV program

A network system availability checker for remote host
(as example two server over Internet)
https://github.com/Turgon37/netsav
"""

# System imports
import getopt
import logging
import sys

# Projet Import
import netsav

class NetsavLauncher:
  """A launcher of the netsav program, run a netsav instance with custom args
  
  Use a both system shell arg and static configuration to run a netsav instance
  See usage function below
  """

  def __init__(self):
    """Constructor : Build an launcher for netsav
    """
    self._program = None
    self._argv = None
    self._conf = dict()
    self._conf['background'] = False
    self._conf['pidfile'] = '/var/run/netsav/netsav.pid'
    self._conf['configfile'] = '/etc/netsav.conf'
    self._conf['log_level'] = 'INFO'

  def showVersion(self):
    """Shows the program version
    """
    print("netsav version v"+netsav.version)

  def showUsage(self):
    """Prints command line options
    """
    print('Usage: '+self._argv[0]+' [OPTIONS...]')
    print('')
    print('NETwork System Availability Verifier v'+netsav.version)
    print('')
    print('Options :')
    print('    -f, --foreground       run the server on the foreground'
            +' (do not daemonize) (default)')
    print('    -b, --background       run in the background (daemonize)')
    print('    -d, --debug            show more debug information about server'
            +'running')
    print('    -c <FILE>              path of the configuration file'
            +'(default to '+self._conf['configfile']+')')
    print('    -p <FILE>              path of the pidfile'
            +'(default to '+self._conf['pidfile']+')')
    print('    -h, --help             display this help message')
    print('    -V, --version          print the version')

  def _parseCmdLineOptions(self, options_list):
    """Parse input main options, and apply rules
    
    @param(dict) options_list : array of option key => value
    """
    for opt in options_list:
      if opt[0] in ['-b', '--background']:
        self._conf['background'] = True
      if opt[0] in ['-f', '--foreground']:
        self._conf['background'] = False
      if opt[0] == '-c':
        self._conf['configfile'] = opt[1]
      if opt[0] == '-p':
        self._conf['pidfile'] = opt[1]
      if opt[0] in ['-d', '--debug']:
        self._conf['log_level'] = 'DEBUG'
      if opt[0] in ['-h', '--help']:
        self.showUsage()
        sys.exit(0)
      if opt[0] in ['-V', '--version']:
        self.showVersion()
        sys.exit(0)

  def start(self, argv):
    """ Entry point of the launcher
    
    @param(dict) argv : array of shell options given by main function
    """
    # save the arg vector
    self._argv = argv

    # read the only allowed command line options
    try:
      cmd_short_opts = 'hbfdVp:c:'
      cmd_long_opts = ['help', 'version', 'background', 'foreground', 'debug']
      given_options_list, args = getopt.getopt(argv[1:], cmd_short_opts, cmd_long_opts)
    except getopt.GetoptError:
      self.showUsage()
      sys.exit(-1)

    self._parseCmdLineOptions(given_options_list)

    try:
      self._program = netsav.Netsav(self._conf['background'],
                            self._conf['configfile'],
                            self._conf['log_level'])
      return self._program.start(self._conf['pidfile'])
    except Exception as e:
      logging.getLogger('netsav-launcher').exception(e)
      return False


##
# Run launcher as the main program
if __name__ == '__main__':
  launcher = NetsavLauncher();
  if launcher.start(sys.argv):
    sys.exit(0)
  else:
    sys.exit(-1)
