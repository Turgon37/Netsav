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

"""NETSAV - NETwork System Availability Verifier

This module provide a network system availability checker for remote host.
Available on : https://github.com/Turgon37/Netsav

This module provide a python daemon that consists in a server object and\nseveral client possible client object.
With that a trigger module provide a way to handle netsav's event by the way\nof your choice. In other word you can build your own trigger class,\nthey are loaded dynamically according to configuration file.

CONFIGURATION :
The configuration file contains these sections :

  * The first section name are fixed and reserved for module you cannot use them\nfor client naming :

[MAIN] : reserved to module configuration

[SERVER] : passed to server class during server instanciation

[DEFAULT] : the defaults values for clients objects

  * These section (which start with TRIGGER string) define a trigger handling :

[TRIGGER_*] : the string which follow the 'TRIGGER_' string is use to load the\n python class. To make your own python trigger you can use the given skeleton

  * All other name correspond to client declarations
[*] : override the default values for client objects and define a\nnew client with the name of the section.

USAGE:
To use this module you can :

  use the netsav-launcher class which is provided with the github project

   or

  put the following code into your python launcher :
>>> import netsav
>>> instance = netsav.Netsav( (bool)daemonize?, (string)loglevel )
>>> instance.load( (string)configuration file )
>>> instance.start( (string)pid file )
"""

# Project imports
from . import netsav
from .version import version
from .netsav import Netsav

__all__ = ['netsav', 'config', 'version', 'sync', 'trigger']
