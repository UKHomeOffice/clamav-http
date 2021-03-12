#!/bin/bash
# 
# Wrapper script that keeps Webserver and AV mirror up to date

set -o errexit

CVDUPDATE_ROOT="${CVDUPDATE_ROOT:-/home/clam/}"
CVDUPDATE_SLEEP="${CVDUPDATE_SLEEP:-5m}"
LIGHTTPD_ROOT="${LIGHTTPD_ROOT:-/home/clam/mirror}"
LIGHTTPD_CONFIG="${LIGHTTPD_CONFIG:-lighttpd.conf}"
FRESHCLAM_CONFIG="${FRESHCLAM_CONFIG:-/etc/clamav/freshclam.conf}"

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
  cvd config set --dbdir $CVDUPDATE_ROOT/db
  cvd config show
  # If this fails dont exit,
  if ! cvd update -V 
    then
      err "CVD update failed, continuing"
      continue
  fi
}

##############################################
# Start webserver
# Globals:
#   LIGHTTPD_CONFIG
# Arguments:
#   None
# Outputs:
#   Writes update log to /var/lib/clamav
##############################################
function lighttpdrun() {
  # Start http server
  log "Starting Lighthttpd"
  lighttpd -t -f $LIGHTTPD_CONFIG
  lighttpd -D -f $LIGHTTPD_CONFIG
}


##############################################
# cvdupdate will run based on an interval
# if new signatures are found they are tested
# with freshclam and synced with mirror 
# Globals:
#   CVDUPDATE_SLEEP
# Locals:
#   None
# Outputs:
#   Writes log to stdout
##############################################
function cvdupdate() {
  while true
    do 
      log "Starting cvdupdate process"
      if ! cvd update -V 
        then
          err "CVD update failed, retrying in $CVDUPDATE_SLEEP"
          sleep $CVDUPDATE_SLEEP
          continue
        else
          if [ $(find $CVDUPDATE_ROOT/db -mmin -2 | wc -l) -ge 1 ] 
            then 
              log "Recent changes found: running self test"
              # Run the selftest, if this fails continue and try later
              if ! selftest
                then
                  err "Self test failed: sleeping"
                  sleep $CVDUPDATE_SLEEP
                  continue
                else 
                log "Self test ok: Publishing signatures to mirror"
                rsync -av --checksum $CVDUPDATE_ROOT/db/* $LIGHTTPD_ROOT/
              fi
              log "Signatures published to mirror"
            else
              log "Definitions up to date"
          fi
      fi
      log "Sleeping"
      sleep $CVDUPDATE_SLEEP
    done
}


##############################################
# selftest prior to publishing 
##############################################
function selftest() {
  log "Self test start"
  cvd serve -V &
  last_pid=$!
  sleep 10
  freshclam --config-file=$FRESHCLAM_CONFIG --stdout 
  sleep 20
  log "Test complete"
  kill $last_pid
}

function main() {
  setup
  cvdupdate &
  lighttpdrun
}


main "@"


