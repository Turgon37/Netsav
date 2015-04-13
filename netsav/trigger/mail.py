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
#import logging
from email.mime.text import MIMEText
import smtplib
from socket import error as socket_error
import socket


# Projet Imports
from netsav.trigger.trigger import TriggerHandler

class Trigger(TriggerHandler):
  """A simple mail trigger which send a mail to someone
  """
    
  def load(self, config = None):
    """Constructor : Build a mail request
    
    @param(dict) config : the dict which contains all required parameters
    @return(boolean) :  True if load success
                        False otherwise
    """
    if not config:
      return False
    
    if 'sender' not in config or 'recipient' not in config:
      if self._logger:
        self._logger.error('Trigger "'+self.getName()+
                  '" need a mail sender and recipient')
      return False
    
    if 'start_tls' not in config:
      config['start_tls'] = false
      
    # check username and password
    if 'auth' in config:
      if config['auth'] in self.BOOL_TRUE_MAP and (
          not 'username' in config or not 'password' in config
          ):
        if self._logger:
          self._logger.error('Trigger "'+self.getName()+
                    '" need a username and password for auth')
        return False
    else:
      config['auth'] = false
      
    if 'tag' not in config:
      config['tag'] = 'NETSAV'
    else:
      config['tag'] = config['tag'].strip('[]')
      
    if 'body' not in config:
      config['body'] = (
        'Hi,\n\n{message}\n\nRegards,\nNETSAV Network monitoring system'
        )
        
    self._config = config
    return True
    
  def do(self, value = None):
    """The run statement function, call when an event must be trigged by this
    
    @return(boolean) :  True if handle success
                        False otherwise
    """
    if not value or not self._config:
      return False

    conf = self._config
    try:
      if conf['ssl'] in self.BOOL_TRUE_MAP:
        m = smtplib.SMTP_SSL(host = conf['server'], 
                              port = conf['port'],
                              timeout = 1)
      else:
        m = smtplib.SMTP(host = conf['server'], 
                          port = conf['port'],
                          timeout = 1)
    except socket_error as e:
      if self._logger:
        self._logger.error('Trigger "'+self.getName()+
                  '" unable to connect to '+conf['server']+':'+conf['port'])
      return False
    
    if conf['start_tls'] in self.BOOL_TRUE_MAP:
      m.starttls()
    if conf['auth'] in self.BOOL_TRUE_MAP:
      m.login(conf['username'], conf['password'])
    
    subject = '['+socket.gethostname()+']['+conf['tag']+']'
    if 'tag' in value:
      subject += '['+value['tag']+']'
    if 'brief' in value:
      subject += ' '+value['brief']
    
    body = conf['body'].replace('\\n','\n').format(message=value['msg'])

    # Building mail
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = conf['sender']
    msg['To'] = conf['recipient']
    m.sendmail(conf['sender'], conf['recipient'].split(','), msg.as_string())
    m.quit()    
    return True