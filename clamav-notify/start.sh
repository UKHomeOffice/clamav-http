#!/bin/bash

FRESHCLAM_ROOT="${FRESHCLAM_ROOT:-/var/lib/clamav}"
FRESHCLAM_CONFIG="${FRESHCLAM_CONFIG:-/etc/clamav/freshclam.conf}"

LIGHTTPD_ROOT="${LIGHTTPD_ROOT:-/var/lib/clamav}"
LIGHTTPD_CONFIG="${LIGHTTPD_CONFIG:-lighttpd.conf}"

mkdir -p $LIGHTTPD_ROOT
touch "$LIGHTTPD_ROOT/index.htm"

freshclam -d --config-file=$FRESHCLAM_CONFIG
lighttpd -t -f $LIGHTTPD_CONFIG
lighttpd -D -f $LIGHTTPD_CONFIG
