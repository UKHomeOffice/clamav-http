FROM alpine:3.13.10

ENV CLAM_VERSION=0.103.6-r0

WORKDIR /clam

RUN apk add --update-cache bash wget curl shadow \
    clamav=$CLAM_VERSION clamav-libunrar=$CLAM_VERSION

RUN adduser -S -g clamav -u 1000 clam \
    && chown -R clam:clamav /clam /var/log/clamav

USER 1000

EXPOSE 3310
