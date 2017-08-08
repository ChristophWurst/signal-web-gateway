FROM golang:alpine as builder

RUN apk --no-cache add mercurial git \
    && go get github.com/janimo/textsecure/ \
    && cd src/github.com/janimo/textsecure/cmd/textsecure \
    && go build \
    && mv /go/src/github.com/janimo/textsecure/cmd/textsecure /output \
    && rm -f /output/main.go

FROM alpine:latest

RUN apk --no-cache add \
      tini \
      py-pip \
      ca-certificates

RUN addgroup -S signal

RUN adduser -S -G signal -h /signal signal

WORKDIR /signal

COPY --from=builder /output /signal

COPY start.py /signal/start.py

USER signal

RUN pip install --user \
      flask \
      gunicorn \
    && rm -rf .cache

ENTRYPOINT ["/sbin/tini", "--"]

CMD ["/signal/.local/bin/gunicorn", "-w", "1", "-b", "0.0.0.0:5000", "start:app"]
