#!/bin/bash

touch /var/lib/clamav/index.htm

freshclam -d
lighttpd -t -f lighttpd.conf
lighttpd -D -f lighttpd.conf
