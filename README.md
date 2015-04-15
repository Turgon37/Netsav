# NETSAV - NETwork System Availability Verifier

This projected is licensed under the terms of the MIT license


A network system availability checker for remote host over Internet (as exemple)

## Usage

The netsav module is independant, but it's provided with a launcher class

Run in command line as normal program :
```bash
  ./netsav-launcher.py [OPTIONS]
```

Use the --help comand to view the usage message and the complete list of options

## Configuration

The configuration is made by the program given config file (option -c)
An example is provided in this repository with all available options keys

[example](config.conf)

For more details about keyword read the comment in given example file.

For all trigger please read the associated readme

#### Lexical

In the program the following word means :

  * **client** : a client is represented by a thread which make http query at a specified interval. It has to maintain the status of the host of which it is in charge. When an event happen, such state change, a trigger action is made
  
  * **server** : a server node which listen http query on local host.
  Is answers with a simple http code
  
  * **reference** : it's a special attribut applied on some client. when a client is declare as reference, it can make trigger event, but simply maintains his associated host status. When the host is down, it disable all other non-refrence client.
  When there are multiple reference, as soon as at least one is down all client are disable. And all reference must be UP to re-enable all client 

  * **trigger** : it refers to a event handler class that is call when a client generate a event. An event is composed of some field in a python dictionnary.
  
  
  

## Hook

You can write your own trigger in trigger directory.
A skeleton example is provided to help you to create an appropriate trigger class. Follow the skeleton to understand all feature such functions return code, function overriding.

All available field in a event are : 
'name', 'address', 'port', 'interval', 'min_retry', 'max_retry', 'tcp_timeout', 'current_state', 'current_state_str', 'previous_state', 'previous_state_str', 'msg', 'brief', 'tag'

To add a new trigger just put your class in the trigger directory.
Add a new section in the configuration file with a name like this [TRIGGER_<NAME>], where <NAME> is the name of your trigger class.
<br />
As example for the mail trigger [TRIGGER_MAIL].

And then put all your specific key option below the section. Each option must be prefixed by your trigger name and a dot.
<br />As example for the mail trigger :
  mail.sender = some@host.com


## Installation

### On debian installation
  You can simply install the provided deb package
    The service can be managed by /etc/init.d/netsav script or by the distribution available command such as ```service```

##### Requires:
  * A Debian based distribution


### In all installation

##### Requires project (a version is provided by this repository):
  * HttpTeepotReply (on https://github.com/Turgon37/HttpTeepotReply)

##### Requires:
  * python3 >= 3.2
  * python3-dev >= 3.2
