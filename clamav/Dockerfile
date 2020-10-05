FROM alpine:3.11

ENV CLAM_VERSION=0.102.3-r0

WORKDIR /clam

RUN apk add --no-cache bash wget shadow

RUN apk add --no-cache clamav=$CLAM_VERSION clamav-libunrar=$CLAM_VERSION

COPY start.sh .

RUN adduser -S -g clamav -u 1000 clam \
    && chown -R clam:clamav /clam /var/log/clamav

USER 1000

EXPOSE 3310
