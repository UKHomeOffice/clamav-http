FROM alpine:3.18

ENV CLAM_VERSION=1.1.2-r0

WORKDIR /clam

# Add edge repository
RUN echo "http://dl-cdn.alpinelinux.org/alpine/edge/community" >> /etc/apk/repositories

RUN apk add --no-cache bash clamav=$CLAM_VERSION clamav-libunrar=$CLAM_VERSION

RUN apk add --no-cache --upgrade openssl

RUN adduser -S -g clamav -u 1000 clam \
    && chown -R clam:clamav /clam /var/log/clamav

USER 1000

EXPOSE 3310
