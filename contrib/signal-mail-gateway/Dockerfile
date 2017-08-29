FROM	debian:stretch

MAINTAINER	morph027<morphsen@gmx.com>

ENV	DEBIAN_FRONTEND noninteractive

RUN	apt-get update \
	&& sh -c 'echo "postfix postfixpostfix/mailname string $HOSTNAME" | debconf-set-selections' \
	&& sh -c 'echo "postfix postfix/main_mailer_type select Local only" | debconf-set-selections' \
	&& apt-get install -y \
		curl \
		mpack \
		postfix \
		inetutils-syslogd \
	&& apt-get clean \
	&& apt-get -y autoremove \
	&& rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

COPY	entrypoint.sh /entrypoint.sh

COPY	mail2signal.sh /usr/local/bin/mail2signal.sh

EXPOSE	25

ENV	TINI_VERSION v0.15.0
ADD	https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini /tini
RUN	chmod +x /tini
ENTRYPOINT	["/tini", "--"]

COPY	entrypoint.sh /entrypoint.sh
RUN	chmod +x /entrypoint.sh
CMD	["/entrypoint.sh"]
