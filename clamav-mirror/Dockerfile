FROM golang:1.26.3-alpine3.23 AS supercronic-build
RUN go install github.com/aptible/supercronic@v0.2.45

FROM python:3.14-alpine3.23

ENV CLAM_VERSION=1.4.4-r0
WORKDIR /clam

# Add community repository for ClamAV
RUN echo "http://dl-cdn.alpinelinux.org/alpine/v3.23/community" >> /etc/apk/repositories

RUN apk update && apk upgrade --no-cache && \
    apk add --no-cache bash curl rsync lighttpd \
    clamav=$CLAM_VERSION clamav-libunrar=$CLAM_VERSION

COPY --from=supercronic-build /go/bin/supercronic /usr/local/bin/supercronic
RUN adduser -S -g clamav -u 1000 clam \
 && chown clam:clamav /usr/local/bin/supercronic \
 && chown -R clam:clamav /clam /var/log/clamav /var/lib/clamav

RUN pip install --no-cache-dir -U setuptools certifi

RUN pip install --no-cache-dir -vv cvdupdate==1.1.1

COPY start.sh lighttpdhost.conf lighttpdmirror.conf test.sh ./
COPY freshclam.conf /etc/clamav/freshclam.conf
COPY cvdmirror.crontab .
COPY files/ ./files/
RUN chmod +x start.sh test.sh
USER 1000

EXPOSE 8080 9090

ENTRYPOINT ["./start.sh"]
