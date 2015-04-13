
# Mail trigger for NETSAV

This python package contains trigger class for add a mail trigger in netsav program

## Usage

Just put mail.py in netsav/trigger directory and declare a section named TRIGGER_MAIL in netsav config file

## Installation

##### Requires:
  * python3 >=
  * A mail server
    with or without authentication
    support tls conversation

## Configuration

Below the list of implemented options :

Boolean value can be : true, True, TRUE, 1 for true mean, all other words considers as false

  * The mail address of the 'from' field
  
```mail.sender = example@domain.org```

  * The (comma separated list of) mail address to which (whose) send mail
  
```mail.recipient = user1@example.org[,user2@example.org]```

  * A string tag to put into bracket in mail subject (after system predefined tag)
  
```mail.tag = NETSAV```

  * The mail body string. Use '\n' for print an newline.
 
  Some keyword can be put into bracket to be parsed : 
  
    {message} replaced by the event message

 
```mail.body = Hi,\n\n{message}\n\nRegards,\nNETSAV Network monitoring system```

  * The smtp server hostname or ip address
  
```mail.server = smpt.domain.org```

  * The smtp server port to use
  
```mail.port = 25```

  * Boolean define if or not to use sasl authentification
  
```mail.auth = true```

  * If auth boolean is true, the username
  
```mail.username = sasl_user```

  * If auth boolean is true, the password
  
```mail.password = sasl_pass```

  * If use tls conversation between client and server
  
```mail.start_tls = true```

  * Use ssl connection (NOT TESTED)
  
```mail.ssl = false```


Found below a complete example of line to add in config.conf

```
[TRIGGER_MAIL]
mail.sender = example@domain.org
mail.recipient = user1@example.org
mail.tag = NETSAV
mail.body = Hi,\n\n{message}\n\nRegards,\nNETSAV Network monitoring system
mail.server = smpt.domain.org
mail.port = 25
mail.auth = true
mail.username = sasl_user
mail.password = sasl_pass
mail.start_tls = true
mail.ssl = false
```

## Todo
  1. Test ssl conversation
  2. add a timeout to smtpib instance in mail trigger
