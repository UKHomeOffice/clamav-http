# clamav-http
Clamav instance with http api. To supersede https://github.com/UKHomeOffice/docker-clamav

## Installation

Basic installation can be acheived by running:

```
helm install -n <namespace> clamav ./charts/clamav
```

Clamav will be installed in the namespace and available at https://clamav/

More detailed documentation on the helm chart can be found [here](/charts/clamav/README.md)

## Components

clamav-http is made up of four components, clamav, clamav-http, clamav-notify and clamav-notify-cron and is designed to be deployed as a service in kubernetes via its helm chart.

### clamav

An extremely barebones clamav/freshclam image with no config. Expects configuration files to be provided at /etc/clamav/clamd.conf and /etc/clamav/freshclam.conf via kubernetes configmaps, docker volumes, or similar

### [clamav-http](/clamav-http/README.md)

Written in golang, provides an http based api to clamav

### clamav-notify

Provides an in cluster mirror to improve startup times for clamav instances, test downloaded signatures and update the clamav deployment in order to trigger rollouts of new signatures.

Requires a service account with permissions to patch the main clamav-deployment

### clamav-notify-cron

clamav-notify-cron is responsible for triggering the image mirroring and updating functonality of clamav-notify

Requires a servce account with permissions to exec into the clamav-notify image