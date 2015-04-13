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

"""Specific configuration parser for NETSAV module

It provide a parser class which extend the original ConfigParser class
in order to add some function, expecially for retrieving directly
several configuration keys in a dict
"""

# System imports
import grp
import logging
import pwd
import re
import sys

# Project imports
from configparser import ConfigParser
from configparser import Error

# Global project declarations
system_logger = logging.getLogger('netsav')

class NetsavConfigParser(ConfigParser):
  """(extend ConfigParser) Set specific function for configuration file parsing
  
  Refer to the config file
  provide more function to parse directly the config file as project's needed
  """

  ## CLASS CONSTANTS
  SERVER_SECTION = 'SERVER'
  DEFAULT_SECTION = 'DEFAULT'
  MAIN_SECTION = 'MAIN'
  TRIGGER_SECTION_REGEX = '^TRIGGER.*$'
  IGNORE_SECTIONS = [SERVER_SECTION, 
                      DEFAULT_SECTION,
                      MAIN_SECTION]

  IPV4_REGEX = '^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$'
  DN_REGEX = '^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$'

  LOGLEVEL_MAP = ['ERROR', 'WARN', 'INFO', 'DEBUG']
  # value considered as True in the config file
  BOOL_TRUE_MAP = ['true', 'TRUE', 'True', '1']

  def __init__(self, file = None):
    """Constructor : init the config parser with a config file path
    
    @param(string) file : the path of the config file
    """
    ConfigParser.__init__(self)
    self._config_file = file
    
    # boolean that indicates if the configparser is available
    self._is_config_loaded = False

  def load(self):
    """Try to load the configuration file
    
    @param(string) pidfile : pidfile's path
    @return(boolean) : True if loading is sucess
                        False if loading fail
    """
    # if file is defined
    if not self._config_file is None:
      try:
        if self._config_file in self.read(self._config_file):
          self._is_config_loaded = True
          return True
      except Error as e:
        print(e, file=sys.stderr)
        return False
    return False
  
  def isLoaded(self):
    """Return the load state of this config parser
    
    @return(boolean) : the boolean that indicates if the config
              file is loaded or not 
    """
    return self._is_config_loaded
    
  def getClientSection(self):
    """Return the list of client section name
    
    @return(list) : the list of client sections string
    """
    c_list = [];
    for sect in self.sections():
      if sect not in self.IGNORE_SECTIONS and        re.match(self.TRIGGER_SECTION_REGEX, sect) is None:
        c_list.append(sect)
    return c_list
    
  def getTriggerSection(self):
    """Return the list of trigger section name
    
    @return(list) : the list of trigger sections name
    """
    c_list = [];
    for sect in self.sections():
      if re.match(self.TRIGGER_SECTION_REGEX, sect) is not None:
        c_list.append(sect)
    return c_list

  def getOptLogLevel(self, default = 'INFO'):
    """Return loglevel option from configuration file
    
    @param(string) default : the default value to return if nothing is found
                            in the config file
    @return(string) : the loglevel
    """
    # get a dict with complete section key=>value
    config_dict = dict( self.items(self.MAIN_SECTION) )

    # address option not defined
    if 'log_level' not in config_dict:
      return default
    # defined => check address format
    else:
      if config_dict['log_level'] not in self.LOGLEVEL_MAP:
        system_logger.error("Incorrect loglevel : '%s' must be in ",
                              config_dict['loglevel'], self.LOGLEVEL_MAP)
        return default
      else:
        return config_dict['log_level']

  def getOptLogTarget(self, default = 'STDOUT'):
    """Return logtarget option
    
    @param(string) default : the default value to return if nothing is found
                            in the config file
    @return(string) : the logtarget
    """
    config_dict = dict( self.items(self.MAIN_SECTION) )
    # option is not given
    if 'log_target' not in config_dict:
      return default
    # return given option
    else:
      return config_dict['log_target']
  
  def getOptIgnoreOwn(self):
    """Return ignore_own option
    
    @return(boolean) : the value of the option
    """
    return self._getBooleanFromSection(self.MAIN_SECTION,
                                          'ignore_own')
                                          
  def getOptUid(self):
    """Return the uid (int) option from configfile
    
    @return(int/None): integer : the numeric value of 
                        None: if group is not defined
    """
    user = self.get(self.MAIN_SECTION, 'user', fallback = None)
    if not user:
      return None
    try:
      return pwd.getpwnam(user).pw_uid
    except KeyError:
      system_logger.error("Incorrect username '%s' read in configuration file",
                            user)
      return None
    
  def getOptGid(self):
    """Return the gid (int) option from configfile
    
    @return(int/None): integer : the numeric value of group id
                        None: if group is not defined
    """
    group = self.get(self.MAIN_SECTION, 'group', fallback = None)
    if not group:
      return None
    try:
      return grp.getgrnam(group).gr_gid
    except KeyError:
      system_logger.error("Incorrect groupname '%s' read in configuration file",
                            group)
      return None

  def getServerConfigDict(self):
    """Return a minimal dict contains server bind parameters
    
    Get the dict that contains only network information for server binding
    """
    server_config_dict = dict()
    server_config_dict['address'] = self._getIpAddressFromSection(
                                          self.SERVER_SECTION)
    server_config_dict['port'] = self._getIntFromSection(
                                          self.SERVER_SECTION, 'port')
    server_config_dict['log_client'] = self._getBooleanFromSection(
                                          self.SERVER_SECTION,
                                          'log_client',
                                          default = True)
    return server_config_dict

  def getTriggerConfigDict(self, section):
    """Return the dict which contains all value which match with the 'name.'
    
    @return(dict) : the parameters dict
    """
    config_dict = dict( self.items(section) )
    trig_dict = dict()
    trig_dict['name'] = section.partition('_')[2].lower()
    for opt in config_dict:
      if re.match(trig_dict['name']+'.*', opt) is not None:
        opt_name = opt.partition('.')[2]
        trig_dict[opt_name] = config_dict[opt]
    return trig_dict

  def getClientConfigDict(self):
    """Return a dict which contains each client configuration dict
     
    The first dict is indexed by config file clients sections (client name),
      these sections are named with clients name and contain default values
      overwrite by specific value
    The second level dict contains only each network parameter needed by a    
    client
    @return(dict(dict)) : a dict of dict
    """
    
    client_all_config_dict = dict()
    for client_section in self.sections():
      if client_section in self.getClientSection():
        system_logger.debug("Loading configuration section for client : %s",
                              client_section)
        c_conf = dict()
        c_conf['name'] = client_section
        c_conf['address'] = self._getAddressFromSection(client_section)
        c_conf['port'] = self._getIntFromSection(client_section, 'port')
        c_conf['interval'] = self._getIntFromSection(client_section, 'interval')
        c_conf['tcp_timeout'] = self._getIntFromSection(client_section,     
                                                        'tcp_timeout',
                                                        default = 1)
        c_conf['min_retry'] = self._getIntFromSection(client_section,   
                                                        'min_retry',
                                                        default = 1)
        c_conf['max_retry'] = self._getIntFromSection(client_section, 
                                                      'max_retry',
                                                      default = 3)
        c_conf['query_method'] = self.get(client_section,
                                            'query_method',
                                            fallback = 'HEAD')

        # Add to master dict
        client_all_config_dict[client_section] = c_conf
        system_logger.debug("read conf = %s", c_conf)

    return(client_all_config_dict)

  def _getIpAddressFromSection(self, section = 'DEFAULT',
                                      option = 'address', 
                                      default = '0.0.0.0', 
                                      version = 4):
    """Return 'address' IP only option from configuration file section specified
    
    @param(string) section : name of the file section in which
    @param(string) option : name of the key which contain address
    @param(string) default : the default string to return if option
                              is not declare
    @param(integer) version : version of IP protocol for secure address matching
                                (default=4)
    @return(string) : IP address is it is correct
                      None otherwise
    """
    if option is None:
      return None
    config_dict = dict(self.items(section))

    # address option not defined
    if option not in config_dict:
      return default
    # check address format
    if version == 4:
      regexp = self.IPV4_REGEX
    else:
      regexp = '^$'

    if re.match(regexp, config_dict[option]) is None:
      system_logger.error("Incorrect bind address read in configuration file: '%s'",  config_dict[option])
      return None

    return config_dict[option]

  def _getAddressFromSection(self, section = 'DEFAULT', 
                                    option = 'address',
                                    default = '0.0.0.0',
                                    version = 4):
    """Return 'address' IP or DN option from configuration file
    
    @param(string) section : name of the file section in which
    @param(string) option : name of the key which contain address
    @param(string) default : the default object to return if option is not 
                              declare
    @param(integer) version : version of IP protocol for secure address matching
                              default=4
    @return(string) : address is it is correct
                       None otherwise
    """
    if option is None:
      return None
    config_dict = dict(self.items(section))

    # address option not defined
    if option not in config_dict:
      return default

    # check address format
    # Check if DN string
    if re.match(self.DN_REGEX, config_dict[option]) is None:
      if version == 4:
        regexp = IPV4_REGEX
      else:
        regexp = '^$'

      # Check if IPv4
      if re.match(regexp, config_dict[option]) is None:
        system_logger.error("Incorrect bind address read in configuration file: '%s'", config_dict[option])
        return None

    return config_dict[option]

  def _getIntFromSection(self, section = 'DEFAULT', 
                                option = None,
                                default = None):
    """Return integer 'value' of 'option' from configuration file
    
    @param(string) section : name of the file section in which search the option
    @param(string) option : name of the section option from which to try to read an int
    @param(string) default : the default string to return if option is not declare
    @return(string) : value if it is correct
                     None if it is not a int
    """
    if option is None:
      return None
    config_dict = dict(self.items(section))

    # value not defined
    if option not in config_dict:
      return default
    # check value
    else:
      try:
        return self.getint(section, option)
      except ValueError:
        system_logger.error("Incorrect option '%s' read in configuration file: '%s'", option, config_dict[option])
        return None

  def _getBooleanFromSection(self, section = 'DEFAULT', 
                                option = None,
                                default = False):
    """Return a boolean value from config file
    
    @param(string) section : name of the file section in which search the option
    @param(string) option : name of the section option from which to try to read a boolean
    @param(string) default : the default string to return if option is not declare
    @return(string) : True or False
    """
    if option is None:
      return default
    # get a dict with complete section key=>value
    config_dict = dict(self.items(section))
    # value not defined
    if option not in config_dict:
      return default
    # check value
    else:
      if config_dict[option] in self.BOOL_TRUE_MAP:
        return True
      else:
        return False
