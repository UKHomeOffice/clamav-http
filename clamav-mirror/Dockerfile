FROM python:alpine3.13

ENV CLAM_VERSION=0.103.1-r0

WORKDIR /clam

RUN apk add --update-cache bash vim wget shadow curl rsync lighttpd \
    clamav=$CLAM_VERSION clamav-libunrar=$CLAM_VERSION

RUN adduser -S -g clamav -u 1000 clam \
    && chown -R clam:clamav /clam /var/log/clamav /var/lib/clamav

COPY requirements.txt ./

RUN pip install -r requirements.txt

COPY notify.py start.sh lighttpd.conf mirror.sh ./
COPY freshclam.conf /etc/clamav/freshclam.conf
COPY files/ ./files/

USER 1000

EXPOSE 8080

ENTRYPOINT ["./mirror.sh"]
