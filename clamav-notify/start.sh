#!/bin/bash
# 
# Starts AV mirror and seeds with latest definitions if they dont already exist

set -o errexit

FRESHCLAM_ROOT="${FRESHCLAM_ROOT:-/var/lib/clamav}"
FRESHCLAM_CONFIG="${FRESHCLAM_CONFIG:-/etc/clamav/freshclam.conf}"
LIGHTTPD_ROOT="${LIGHTTPD_ROOT:-/var/lib/clamav/mirror}"
LIGHTTPD_CONFIG="${LIGHTTPD_CONFIG:-lighttpd.conf}"


function err() {
  echo "[$(date +'%Y-%m-%dT%H:%M:%S%z')]: $@" >&2
}


function log() {
  echo "[$(date +'%Y-%m-%dT%H:%M:%S%z')]: $@"
}


function showconfig() {
  log "Freshclam root: $FRESHCLAM_ROOT"
  log "Freshclam config: $FRESHCLAM_CONFIG"
  log "Lighttpd root: $LIGHTTPD_ROOT"
  log "Lighttpd config: $LIGHTTPD_CONFIG"
  cat $LIGHTTPD_CONFIG
  cat $FRESHCLAM_CONFIG
}


##############################################
# Create directories to host mirror, copy over
# defs if applicable and start daemon.
# Globals:
#   LIGHTHTTPD_ROOT
#   FRESHCLAM_ROOT
#   FRESHCLAM_CONFIG 
#   FRESHCLAM_ROOT
# Arguments:
#   None
# Outputs:
#   Writes log to stdout
##############################################
function startmirror() {
  mkdir -p $LIGHTTPD_ROOT
  touch "$LIGHTTPD_ROOT/index.htm"
  # Run freshclam in foreground once to get latest defs on container start
  freshclam --config-file=$FRESHCLAM_CONFIG --stdout
  # If no defs exist in mirror, copy them
  yes n | cp -i $FRESHCLAM_ROOT/*.cvd $LIGHTTPD_ROOT 2>/dev/null
  # Set freshclam to run in background
  freshclam -d --config-file=$FRESHCLAM_CONFIG
  # Start http server
  lighttpd -t -f $LIGHTTPD_CONFIG
  lighttpd -D -f $LIGHTTPD_CONFIG
}


function main() {
  showconfig
  startmirror
}

main "@"