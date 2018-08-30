#!/bin/bash

start() {
  /signal/.local/bin/gunicorn -w  1 -b 0.0.0.0:5000 start:APP
}

stop() {
  echo "[ERROR] It looks like your Signal identity has not been setup properly, please follow instructions on how to register an account"
}

entrypoint() {
  sudo chown -R 1000:1000 .storage .config
  if [ -f /signal/.storage/identity/identity_key ]; then
    start
  else
    stop
  fi
}

if [ ! -z "$1" ]; then
  case "$1" in
    "register")
      ./textsecure
    ;;
    "*")
      entrypoint
    ;;
  esac
else
  entrypoint
fi
