#!/bin/bash

touch /var/lib/clamav/index.htm

freshclam -d -c 48 --on-update='python notify.py'
lighttpd -D -f lighttpd.conf