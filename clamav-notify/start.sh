#!/bin/bash

touch /var/lib/clamav/index.htm

freshclam -d -c 48 --on-update='python notify.py'
lighttpd -t -f lighttpd.conf
lighttpd -D -f lighttpd.conf