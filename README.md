# clamav-http2
Clamav instance with http api. To supersede https://github.com/UKHomeOffice/docker-clamav


## Installation

Basic installation can be achieved by running:

```
helm install -n <namespace> clamav ./charts/clamav
```

Clamav will be installed in the namespace and available at https://clamav/

More detailed documentation on the helm chart can be found [here](/charts/clamav/README.md)

## Components

clamav-http is made up of three components, clamav, clamav-http and clamav-mirror and is designed to be deployed as a service in kubernetes via its helm chart.

### clamav

An extremely barebones clamav/freshclam image with no config. Expects configuration files to be provided at /etc/clamav/clamd.conf and /etc/clamav/freshclam.conf via kubernetes configmaps, docker volumes, or similar.

This container has ClamD which exposes a TCP port that is use to scan files from the clamav-http container golang server.
It also fetches the database signatures from the configured private mirror (clamav-mirror)

### [clamav-http](/clamav-http/README.md)

Written in golang, provides an http-based api to the ClamD TCP port and is exposed to tenants.

### clamav-mirror

Provides a private in-cluster mirror to clamav signatures improve startup times for clamav instances and consistency of signature versions.

The mirror utilises the recently released cvdupdate (python) tool with cron scheduling by superchronic. Definition updates are smoke tested prior to publishing. The status of cronjobs are published as prometheus metrics.
- start.sh - container entrypoint, configures cvd (signature db downloader), sets up supercronic (cron scheduler) and lighthttpd.
- test.sh - cron job that tests the most recently downloaded signature database from /home/clam/db runs freshclam on it and if successful it will copy the files over to /home/clam/mirror which is downloaded by the clamav instances. The only reason ClamAV is installed in this container at all is to test it in this script.


