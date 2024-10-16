FROM python:3.11-alpine3.20

ENV CLAM_VERSION=1.3.2-r0
ENV SUPERCRONIC_URL=https://github.com/aptible/supercronic/releases/download/v0.2.30/supercronic-linux-amd64 \
    SUPERCRONIC=supercronic-linux-amd64 \
    SUPERCRONIC_SHA1SUM=9f27ad28c5c57cd133325b2a66bba69ba2235799

WORKDIR /clam

# Add edge repository
RUN echo "http://dl-cdn.alpinelinux.org/alpine/edge/community" >> /etc/apk/repositories

RUN apk update && apk add --no-cache bash curl rsync lighttpd \
    clamav=$CLAM_VERSION clamav-libunrar=$CLAM_VERSION && \
    apk upgrade --no-cache

RUN adduser -S -g clamav -u 1000 clam \
    && chown -R clam:clamav /clam /var/log/clamav /var/lib/clamav

RUN curl -fsSLO "$SUPERCRONIC_URL" \
 && echo "${SUPERCRONIC_SHA1SUM}  ${SUPERCRONIC}" | sha1sum -c - \
 && chmod +x "$SUPERCRONIC" \
 && chown clam:clamav "$SUPERCRONIC" \
 && mv "$SUPERCRONIC" "/usr/local/bin/${SUPERCRONIC}" \
 && ln -s "/usr/local/bin/${SUPERCRONIC}" /usr/local/bin/supercronic

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
