#!/bin/sh

start() {
  /signal/.local/bin/gunicorn -w  1 -b 0.0.0.0:5000 start:APP
}

stop() {
  echo "[ERROR] It looks like your Signal identity has not been setup properly, please follow instructions on how to register an account"
}

[ -f /signal/.storage/identity/identity_key ] && start || stop
