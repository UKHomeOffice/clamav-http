FROM alpine:3.24.1

ENV CLAM_VERSION=1.4.6-r0

WORKDIR /clam

# Add community repository for ClamAV
RUN echo "http://dl-cdn.alpinelinux.org/alpine/v3.24/community" >> /etc/apk/repositories

RUN apk update && apk upgrade --no-cache

RUN apk add --no-cache bash clamav=$CLAM_VERSION clamav-libunrar=$CLAM_VERSION

RUN apk add --no-cache --upgrade openssl

RUN adduser -S -g clamav -u 1000 clam \
    && chown -R clam:clamav /clam /var/log/clamav

USER 1000

EXPOSE 3310
