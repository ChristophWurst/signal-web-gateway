# Signal Web Gateway

Putting [janimo's](https://github.com/janimo/textsecure) Signal client behind a web server to have a web gateway for other apps (reporting, monitoring, ...).

You might want to check the [wiki](https://gitlab.com/morph027/signal-web-gateway/wikis/home) for more stuff (like a signal-web-gateway addon).

This setup runs in Docker, so you can easily throw it into your swarm. If you want to run it standalone, just have a look at the bottom of this page.

## Prepare config and storage

If you do not already have a config file, just create one like this:

```
mkdir .config .storage
touch .config/contacts.yml
docker run --rm -it registry.gitlab.com/morph027/signal-web-gateway:master cat .config/config.yml > .config/config.yml
sudo chown -R 1000:1000 .config .storage # needs to belong to signal user
```

## Register

Now you need to register like described at [janimo's wiki](https://github.com/janimo/textsecure/wiki/Installation). This could be done via SMS or Voice (for SIP numbers)
Edit the `.config/config.yml` to suit your needs and start the registration:

```
docker run --rm -it -v $PWD/.config:/signal/.config -v $PWD/.storage:/signal/.storage registry.gitlab.com/morph027/signal-web-gateway:master /bin/sh
./textsecure
# confirm code
# ctrl+c
# ctrl+d
```

A cool way to register test numbers is [SMSReceiveFree](https://smsreceivefree.com/).

## Run

```
docker run -d --name signal-web-gateway --restart always -v $PWD/.config:/signal/.config -v $PWD/.storage:/signal/.storage -p 5000:5000 registry.gitlab.com/morph027/signal-web-gateway:master
```

## Access

Now you can just use curl to send messages using the form data `to`, `message`, `file` (optionally) and `group` (optionally):

* Plain text (assuming you're running against the docker container at your machine):

```
curl -X POST -F "to=+1337" -F "message=Test" http://localhost:5000
```

* Text message with attachement (assuming you're running against the docker container at your machine):

```
curl -X POST -F file=@some-random-cat-picture.gif -F "to=+1337" -F "message=Test" http://localhost:5000
```

* Send to groups (assuming you're running against the docker container at your machine):

```
curl -X POST -F "to=ff702f10bebfa2f1508deb475ded2d65" -F "message=Test" http://localhost:5000
```

You can retrieve the groupid by having a look into `.storage/groups`

## Security

You might want to run this behind an reverse proxy like nginx to add some basic auth or (much better) run this inside Docker swarm with [Docker Flow Proxy](https://proxy.dockerflow.com) and [basic auth](https://proxy.dockerflow.com/swarm-mode-auto/#service-authentication) using secrets.

## Standalone

If you want to run this without Docker, you need to setup:

* janimo's [go binary]([wiki](https://gitlab.com/morph027/signal-web-gateway/wikis/home))
* a dedicated user
* a python virtualenv for this user
* python requirements
* app
* startup script (e.g. systemd unit file)

### User

```
useradd -s /bin/bash -m signal
```

### Virtualenv + requirements

```
sudo -u signal -H virtualenv /home/signal/virtualenv
sudo -u signal -H pip install flask gunicorn
```

### App

```
sudo -u signal -H git clone https://gitlab.com/morph027/signal-web-gateway /home/signal/signal-web-gateway
```

### Startup

`/etc/systemd/system/signal-web-gateway.socket`:

```
[Unit]
Description=signal-web-gateway gunicorn socket

[Socket]
ListenStream=/run/signal-web-gateway/socket

[Install]
WantedBy=sockets.target
```

`/etc/systemd/system/signal-web-gateway.service`:

```
[Unit]
Description=signal-web-gateway daemon
Requires=signal-web-gateway.socket
After=network.target

[Service]
PIDFile=/run/signal-web-gateway/pid
User=signal
Group=signal
RuntimeDirectory=signal-web-gateway
WorkingDirectory=/home/signal/signal-web-gateway
ExecStart=/home/signal/virtualenv/bin/gunicorn --pid /run/signal-web-gateway/pid --bind unix:/run/signal-web-gateway/socket signal-web-gateway:app
ExecReload=/bin/kill -s HUP $MAINPID
ExecStop=/bin/kill -s TERM $MAINPID
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```
