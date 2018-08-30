# Signal Web Gateway

Putting [janimo's](https://github.com/janimo/textsecure) Signal client behind a web server to have a web gateway for other apps (reporting, monitoring, ...).

You might want to check the [wiki](https://gitlab.com/morph027/signal-web-gateway/wikis/home) for more stuff (like a mail-2-signal addon).

This setup runs in Docker, so you can easily throw it into your swarm or run via docker-compose. If you want to run it standalone, just have a look at the bottom of this page.

**You will need a spare phone number to use for registration!** (SIP numbers are fine)

## Prepare config and storage

* create volumes for the app:

```bash
docker volume create signal-web-gateway_config
docker volume create signal-web-gateway_storage
```

* if you do not already have a config file, just create one (and copy into the volume using a little "workaround"):

```bash
docker run --rm -it registry.gitlab.com/morph027/signal-web-gateway:master cat .config/config.yml > config.yml
docker create -v signal-gateway-config:/signal/.config --name helper alpine:latest
docker cp config.yml helper:/signal/.config/
docker rm helper
```

## Register

Now you need to register your client with the signal servers. This could be done via SMS or Voice (e.g. for SIP numbers). **Do not use your current mobile phone number or it's account will be invalidated!**
Edit the `.config/config.yml` to suit your needs (e.g. add your phone number and select `voice` or `sms` as authentication method) and start the registration:

```bash
docker run --rm -it -v signal-web-gateway_config:/signal/.config -v signal-web-gateway_storage:/signal/.storage registry.gitlab.com/morph027/signal-web-gateway:master register
Enter verification code>
# confirm code
# ctrl+c
# ctrl+d
```

## Run

### Docker Compose

```bash
docker-compose -p signal-web-gateway up -d
```

### Docker

```bash
docker run -d --name signal-web-gateway --restart always -v signal-web-gateway_config:/signal/.config -v signal-web-gateway_storage:/signal/.storage -p 127.0.0.1:5000:5000 registry.gitlab.com/morph027/signal-web-gateway:master
```

## Access

### Multipart form data (w/ image upload)

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

You can retrieve the groups hexid at `/groups` or by having a look into `.storage/groups`:

```bash
$ curl -s http://localhost:5000/groups | jq .
100    83  100    83    0     0   8300      0 --:--:-- --:--:-- --:--:--  8300
{
  "groups": {
    "f441...ad8a": {
      "name": "Foo"
    },
    "ccab...0257": {
      "name": "Bar"
    }
  },
  "success": true
}
```

### JSON data to specific path

If your sending app for whatever reasons is unable to specify form values and just posts json webhooks (Influx Kapacitor, Gitlab webhooks), you can post this data to a path containing the recipient (e.g. `/+1337` or `/ff702f10bebfa2f1508deb475ded2d65`).
The gateway then tries to send the value from json key defined in environment variable `JSON_MESSAGE`.

Example:

```
curl -X POST -d '{"message":"foo"}' http://localhost:5000/+1337
```

### Rekey in case of re-installing Signal

If you (or someone) has re-installed Signal (or switched to a new mobile), the Signal app and the servers will create new keys and this gateway refuses to send messages due to the changed key. You can send a `DELETE` request to `/<recipient>` to delete the old key and receive messages again.

```
curl -X DELETE http://localhost:5000/491337420815
```

## Security

You might want to run this behind an reverse proxy like nginx to add some basic auth or (much better) run this inside Docker swarm with [Docker Flow Proxy](https://proxy.dockerflow.com) and [basic auth](https://proxy.dockerflow.com/swarm-mode-auto/#service-authentication) using secrets.

## Standalone

If you want to run this without Docker, you need to setup:

* aebruno's updated fork of janimo's [go binary](https://github.com/aebruno/textsecure)
* a dedicated user
* a python virtualenv for this user
* python requirements
* the app itself
* startup script (e.g. systemd unit file)
* reverse proxy (in case you want to secure using basic auth and tls, ...)

### User

```
useradd -s /bin/bash -m signal
```

### Virtualenv + requirements

```
sudo -u signal -H virtualenv /home/signal/virtualenv
sudo -u signal -H pip install -r requirements.txt
```

### App

```
sudo -u signal -H git clone https://gitlab.com/morph027/signal-web-gateway /home/signal/signal-web-gateway
```

### Startup

This is an example which listens on a socket fot it's reverse proxy

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

### Reverse proxy

As there are plenty of proxy or webservers (e.g. nginx, apache, caddy, traefik,...), just pick your favourite one. Make sure to proxy requests to the socket at `/run/signal-web-gateway/socket`.
