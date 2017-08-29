#!/bin/bash

set -e

# create unique folder per mail
UUID=$(mktemp -d /tmp/XXXXXXXXXX)

# extract mail
munpack -C "$UUID"
# get attachement if exists
FILE=$(find "$UUID" -name '*.jpg')
# get text message if exists
MESSAGE=$(find "$UUID" -name '*.desc')

# trigger webhook
if [ ! "$MESSAGE" == "" ]; then
  REQUEST="curl -X POST -F to=$RECIPIENT -F message=$(cat $MESSAGE) $SIGNAL_GW"
  if [ ! "$FILE" == "" ]; then
    REQUEST="$REQUEST -F file=@$FILE"
  fi
  eval "$REQUEST"
fi

# delete mail
rm -rf "$UUID"
