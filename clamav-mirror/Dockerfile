FROM python:alpine3.13

ENV CLAM_VERSION=0.103.1-r0
ENV SUPERCRONIC_URL=https://github.com/aptible/supercronic/releases/download/v0.1.12/supercronic-linux-amd64 \
    SUPERCRONIC=supercronic-linux-amd64 \
    SUPERCRONIC_SHA1SUM=048b95b48b708983effb2e5c935a1ef8483d9e3e

WORKDIR /clam

RUN apk add --update-cache bash vim wget shadow curl rsync lighttpd \
    clamav=$CLAM_VERSION clamav-libunrar=$CLAM_VERSION

RUN adduser -S -g clamav -u 1000 clam \
    && chown -R clam:clamav /clam /var/log/clamav /var/lib/clamav

RUN curl -fsSLO "$SUPERCRONIC_URL" \
 && echo "${SUPERCRONIC_SHA1SUM}  ${SUPERCRONIC}" | sha1sum -c - \
 && chmod +x "$SUPERCRONIC" \
 && chown clam:clamav "$SUPERCRONIC" \
 && mv "$SUPERCRONIC" "/usr/local/bin/${SUPERCRONIC}" \
 && ln -s "/usr/local/bin/${SUPERCRONIC}" /usr/local/bin/supercronic


COPY requirements.txt ./

RUN pip install -r requirements.txt

COPY start.sh lighttpdhost.conf lighttpdmirror.conf test.sh ./
COPY freshclam.conf /etc/clamav/freshclam.conf
RUN chown clam:clamav /etc/clamav/freshclam.conf
COPY cvdmirror.crontab .
COPY files/ ./files/
RUN chown -R clam:clamav /clam \
  && chmod +x start.sh test.sh
USER 1000

EXPOSE 8080 9090

ENTRYPOINT ["./start.sh"]
