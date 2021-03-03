#!/bin/bash

FRESHCLAM_ROOT="${FRESHCLAM_ROOT:-/var/lib/clamav}"
FRESHCLAM_CONFIG="${FRESHCLAM_CONFIG:-/etc/clamav/freshclam.conf}"

echo "Freshclam root: $FRESHCLAM_ROOT"
echo "Freshclam config: $FRESHCLAM_CONFIG"

cat $FRESHCLAM_CONFIG

LIGHTTPD_ROOT="${LIGHTTPD_ROOT:-/var/lib/clamav/mirror}"
LIGHTTPD_CONFIG="${LIGHTTPD_CONFIG:-lighttpd.conf}"

echo "Lighttpd root: $LIGHTTPD_ROOT"
echo "Lighttpd config: $LIGHTTPD_CONFIG"

cat $LIGHTTPD_CONFIG

mkdir -p $LIGHTTPD_ROOT
touch "$LIGHTTPD_ROOT/index.htm"

freshclam -d --config-file=$FRESHCLAM_CONFIG

lighttpd -t -f $LIGHTTPD_CONFIG
lighttpd -D -f $LIGHTTPD_CONFIG
