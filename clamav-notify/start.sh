#!/bin/bash

LIGHTTPD_ROOT="${LIGHTTPD_ROOT:-/var/lib/clamav}"
LIGHTTPD_CONFIG="${LIGHTTPD_CONFIG:-lighttpd.conf}"

mkdir -p $LIGHTTPD_ROOT
touch "$LIGHTTPD_ROOT/index.htm"

freshclam -d
lighttpd -t -f $LIGHTTPD_CONFIG
lighttpd -D -f $LIGHTTPD_CONFIG
