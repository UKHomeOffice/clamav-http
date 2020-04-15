FROM python:3-alpine

ENV CLAM_VERSION=0.102.1-r0

WORKDIR /clam

RUN apk add --no-cache bash wget shadow lighttpd \ 
  clamav=$CLAM_VERSION clamav-libunrar=$CLAM_VERSION

RUN adduser -S -g clamav -u 1000 clam \
    && chown -R clam:clamav /clam /var/log/clamav

RUN pip install kubernetes

COPY notify.py start.sh lighttpd.conf ./

USER 1000

EXPOSE 3310

ENTRYPOINT ["./start.sh"]
