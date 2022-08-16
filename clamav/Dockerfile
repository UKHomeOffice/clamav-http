FROM alpine:3.15

ENV CLAM_VERSION=0.104.3-r0

WORKDIR /clam

RUN apk add --update-cache clamav=$CLAM_VERSION clamav-libunrar=$CLAM_VERSION

RUN adduser -S -g clamav -u 1000 clam \
    && chown -R clam:clamav /clam /var/log/clamav

USER 1000

EXPOSE 3310
