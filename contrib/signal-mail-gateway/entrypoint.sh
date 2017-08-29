#!/bin/bash

if [ -z "$SIGNAL_GW" ]; then
  echo "SIGNAL_GW not set, exiting"
  exit 1
fi

if [ -z "$RECIPIENT" ]; then
  echo "RECIPIENT not set, exiting"
  exit 1
fi

if [ ! -z "$ALIAS" ]; then
  echo "$ALIAS: \"|/usr/local/bin/mail2signal.sh\"" >> /etc/aliases
  postconf -e "mydestination = \$myhostname, $HOSTNAME, localhost.localdomain, localhost"
  postconf -e "myhostname = $HOSTNAME"
  postconf -e "mynetworks = 0.0.0.0/0"
  postconf -e "inet_interfaces = $(hostname -i)"
  newaliases
else
  echo "ALIAS not set, exiting"
  exit 1
fi

service inetutils-syslogd start
service postfix start

tail -F /var/log/mail.log
