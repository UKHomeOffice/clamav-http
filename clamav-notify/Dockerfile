FROM python:3-alpine

ENV CLAM_VERSION=0.102.4-r1

WORKDIR /clam

RUN apk add --no-cache bash wget shadow lighttpd

RUN apk add clamav=$CLAM_VERSION clamav-libunrar=$CLAM_VERSION

RUN adduser -S -g clamav -u 1000 clam \
    && chown -R clam:clamav /clam /var/log/clamav

COPY requirements.txt ./

RUN pip install -r requirements.txt

COPY notify.py start.sh lighttpd.conf ./

COPY files/ ./files/

USER 1000

EXPOSE 8080

ENTRYPOINT ["./start.sh"]
