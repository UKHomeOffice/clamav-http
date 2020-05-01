#!/bin/bash

FRESHCLAM_ROOT="${FRESHCLAM_ROOT:-/var/lib/clamav}"
LIGHTTPD_ROOT="${LIGHTTPD_ROOT:-/var/lib/clamav}"
LIGHTTPD_CONFIG="${LIGHTTPD_CONFIG:-lighttpd.conf}"

mkdir -p $LIGHTTPD_ROOT
touch "$FRESHCLAM_ROOT/index.htm"
touch "$LIGHTTPD_ROOT/index.htm"

freshclam -d
lighttpd -t -f $LIGHTTPD_CONFIG
lighttpd -D -f $LIGHTTPD_CONFIG
