# clamav-http
Clamav instance with http api. To supersede https://github.com/UKHomeOffice/docker-clamav

## Installation

```
helm install -n <namespace> clamav ./charts/clamav
```

Clamav will be installed in the namespace and available at https://clamav/

## Components

clamav-http is made up of three components, clamav, clamav-http, and clamav-notify and is designed to be deployed as a service in kubernetes via its helm chart.

### clamav

An extremely barebones clamav/freshclam image with no config. Expects configuration files to be provided via kubernetes configmaps.

### [clamav-http](/clamav-http/README.md)

Written in golang, provides an http based api to clamav

### clamav-notify

Provides an in cluster mirror to improve startup times for clamav instances, and additionally updates the clamav deployment in order to trigger rollouts of new signatures.