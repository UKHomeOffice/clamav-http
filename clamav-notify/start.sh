#!/bin/bash

touch /var/lib/clamav/

LIGHTTPD_CONFIG="${LIGHTTPD_CONFIG:-lighttpd.conf}"

freshclam -d
lighttpd -t -f $LIGHTTPD_CONFIG
lighttpd -D -f $LIGHTTPD_CONFIG
