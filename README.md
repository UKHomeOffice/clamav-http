# clamav-http
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


### [clamav-http](/clamav-http/README.md)

Written in golang, provides an http-based api to clamav

### clamav-mirror

Provides a private in-cluster mirror to improve startup times for clamav instances and consistency of signature versions.

The mirror utilises the recently released cvdupdate tool  with cron scheduling by superchronic. Definition updates are smoke tested prior to publishing. The status of cronjobs are published as prometheus metrics.



