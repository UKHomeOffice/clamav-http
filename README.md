# clamav-http
Clamav instance with http api. To supersede https://github.com/UKHomeOffice/docker-clamav

clamav-http is made up of three components, clamav, clamav-http, and clamav-notify and is designed to be deployed as a service in kubernetes via its helm chart.

## clamav

An extremely barebones clamav/freshclam image with no config. Expects configuration files to be provided via kubernetes configmaps.

## [clamav-http](/clamav-http/README.md)

Written in golang, provides two http apis to clamav. The first based on clamav-rest at the / endpoint, the second at the /v2/ endpoint and documented here

## clamav-notify

Provides an in cluster mirror to improve startup times for clamav instances, and additionally updates the clamav deployment in order to trigger rollouts of new signatures.