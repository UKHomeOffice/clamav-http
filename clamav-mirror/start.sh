#!/bin/bash
# 
# Wrapper script that keeps Webserver and AV mirror up to date

set -o errexit

CVDUPDATE_DEST="${CVDUPDATE_DEST:-/home/clam/db}"
LIGHTTPD_ROOT="${LIGHTTPD_ROOT:-/home/clam/mirror}"
LIGHTTPD_HOST_CONFIG="${LIGHTTPD_HOST_CONFIG:-lighttpdhost.conf}"
LIGHTTPD_TEST_CONFIG="${LIGHTTPD_TEST_CONFIG:-lighttpdmirror.conf}"
FRESHCLAM_CONFIG="${FRESHCLAM_CONFIG:-/etc/clamav/freshclam.conf}"
PROMETHEUS_METRIC_LISTEN_PORT="${PROMETHEUS_METRIC_LISTEN_PORT:-9090}"

function err() {
  echo "[$(date +'%Y-%m-%dT%H:%M:%S%z')]: $@" >&2
}

function log() {
  echo "[$(date +'%Y-%m-%dT%H:%M:%S%z')]: $@"
}


##############################################
# Globals:
#   LIGHTHTTPD_ROOT
# Arguments:
#   None
# Outputs:
#   Writes update log to ~/.cvdupdate
##############################################
function setup() {
  mkdir -p $LIGHTTPD_ROOT
  mkdir -p $CVDUPDATE_DEST
  cvd config set --dbdir $CVDUPDATE_DEST
  cvd config show
  # If this fails dont exit as it could be network releated we still want to keep 
  # the mirror up
  if ! cvd update -V 
    then
      err "ERROR CVD update failed, continue"
  fi
  # Perform an initial rsync if mirror is empty
  if [ -z "$(ls $LIGHTTPD_ROOT)" ]; then
    log "INFO Sync mirror"
    rsync -av --checksum --delete $CVDUPDATE_DEST/ $LIGHTTPD_ROOT/
  else
    log "INFO Mirror present"
  fi
  # Setup server root for livenets/readiness probes
  if [[ ! -e $CVDUPDATE_DEST/index.htm ]]
    then
      touch $CVDUPDATE_DEST/index.htm
  fi
  if [[ ! -e $LIGHTTPD_ROOT/index.htm ]]
    then
      touch $LIGHTTPD_ROOT/index.htm
  fi
}

##############################################
# Start webserver
# Globals:
#   LIGHTTPD_CONFIG
# Arguments:
#   configfile
# Outputs:
#   Writes update log to /var/lib/clamav
##############################################
function lighttpdrun() {
  local configfile="$1"
  # Start http server
  log "INFO Starting lighthttpd"
  lighttpd -D -f $configfile
}

function supercronstart() {
  log "INFO Starting supercronic"
  supercronic -passthrough-logs -prometheus-listen-address localhost:$PROMETHEUS_METRIC_LISTEN_PORT cvdmirror.crontab 
} 


function main() {
  setup
  lighttpdrun $LIGHTTPD_HOST_CONFIG &
  lighttpdrun $LIGHTTPD_TEST_CONFIG &
  supercronstart
}


main "@"


