```
docker run -d --name signal-mail-gateway \
--hostname signal-mail-gateway \
-e "SIGNAL_GW=http://the-signal-gateway.example.com" \
-e "RECIPIENT=+1337" \
-e "ALIAS=signal" \
-p 25:25 \
registry.gitlab.com/morph027/signal-web-gateway:mail-gw
