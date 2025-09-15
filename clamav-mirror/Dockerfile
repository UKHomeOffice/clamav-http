FROM golang:1.24.6-alpine3.22 AS supercronic-build
RUN go install github.com/aptible/supercronic@v0.2.34

FROM python:3.13-alpine3.22

ENV CLAM_VERSION=1.4.3-r0
WORKDIR /clam

# Add edge repository

RUN echo "http://dl-cdn.alpinelinux.org/alpine/edge/main" >> /etc/apk/repositories \
 && echo "http://dl-cdn.alpinelinux.org/alpine/edge/community" >> /etc/apk/repositories

RUN apk update && apk add --no-cache bash curl rsync lighttpd \
    clamav=$CLAM_VERSION clamav-libunrar=$CLAM_VERSION && \
    apk upgrade --no-cache

COPY --from=supercronic-build /go/bin/supercronic /usr/local/bin/supercronic
RUN adduser -S -g clamav -u 1000 clam \
 && chown clam:clamav /usr/local/bin/supercronic \
 && chown -R clam:clamav /clam /var/log/clamav /var/lib/clamav

RUN pip install -U setuptools certifi

RUN pip install -vv cvdupdate==1.1.1

COPY start.sh lighttpdhost.conf lighttpdmirror.conf test.sh ./
COPY freshclam.conf /etc/clamav/freshclam.conf
COPY cvdmirror.crontab .
COPY files/ ./files/
RUN chmod +x start.sh test.sh
USER 1000

EXPOSE 8080 9090

ENTRYPOINT ["./start.sh"]
