#!/bin/bash
# 
# Script to test and publish definitions
set -o errexit

CVDUPDATE_DEST="${CVDUPDATE_DEST:-/home/clam/db}"
# CVDUPDATE_SLEEP="${CVDUPDATE_SLEEP:-5m}"
LIGHTTPD_ROOT="${LIGHTTPD_ROOT:-/home/clam/mirror}"
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
function teardown() {
  log "INFO Cleaning local databases"
  rm -f /var/lib/clamav/*
}

##############################################
# Globals:
#   FRESHCLAM_CONFIG
# Arguments:
#   command
# Outputs:
#   Writes log to stdout
##############################################
function testfreshclam() {
  local command

  freshclam --config-file=$FRESHCLAM_CONFIG --stdout $1
}


##############################################
# Publish signatures 
# Outputs:
#   Writes log to stdout
##############################################
function publishsigs() {
  log "INFO Self test PASS: Publishing signatures to mirror"
  if ! rsync -av --checksum --delete $CVDUPDATE_DEST/ $LIGHTTPD_ROOT/
    then
      err "ERROR: Unable to sync mirror"
      exit
  fi
}

##############################################
# Basic test of eicar and clean file 
# Outputs:
#   Writes log to stdout
##############################################
function scantest() {
  log "INFO: Testing for eicar"
  if ! clamscan files/eicar.txt
    then 
      log "PASS"
    else 
      err "ERROR: Unexpected status, expected 1 got $?"
      exit
  fi
  if ! clamscan files/safe.txt
    then 
      err "ERROR Unexpected status, expected 1 got $?"
      exit
    else 
      log "PASS"
  fi
}

##############################################
# Test freshclam updates in defferent ways
# Use for testing only 
# Globals:
#   none
# Locals:
#   None
# Outputs:
#   Writes log to stdout
##############################################
function soaktest() {
  teardown
  testfreshclam
  scantest
  testfreshclam
  scantest
  teardown
  testfreshclam --no-dns
  scantest
  testfreshclam --no-dns
  scantest
  publishsigs
  teardown
}

##############################################
# In operation, run a freshclam from local
# freshclam's local db is not on a PVC
# Globals:
#   none
# Locals:
#   None
# Outputs:
#   Writes log to stdout
##############################################
function main() {
  testfreshclam --no-dns
  scantest --quiet
  publishsigs
}

main "@"
