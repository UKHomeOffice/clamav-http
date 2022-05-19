clamav
======
A Helm chart for deploying a clamav-http service on kubernetes

Current chart version is `0.3.7`

## Chart Values

## Values

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| clamav.certificate.create | bool | `true` | Should a certificate be created for the clamav service |
| clamav.certificate.issuer | object | `{"kind":"ClusterIssuer","name":"platform-ca"}` | The issuer to use when creating a certificate |
| clamav.certificate.secretName | string | `""` | Override the default certificate secret name |
| clamav.freshclam.mirrors | list | `["database.clamav.net"]` | A list of clamav mirrors to be used by the clamav service |
| clamav.image | string | `"quay.io/ukhomeofficedigital/acp-clamav"` | The clamav docker image |
| clamav.limits.connectionQueueLength | int | `200` | Maximum length the queue of pending connections may grow to |
| clamav.limits.fileSize | int | `20` | The largest file size scanable by clamav, in MB |
| clamav.limits.maxThreads | int | `10` | Maximum number of threads running at the same time. |
| clamav.limits.scanSize | int | `100` | The largest scan size permitted in clamav, in MB |
| clamav.limits.sendBufTimeout | int | `500` |  |
| clamav.resources | object | `{"limits":{"cpu":"1500m","ephemeral-storage":"1000M","memory":"3000M"},"requests":{"cpu":"1000m","ephemeral-storage":"500M","memory":"2000M"}}` | The resource requests and limits for the clamav service |
| clamav.scaling.cpuTarget | int | `30` | The target cpu usage percentage for clamav |
| clamav.scaling.maxReplicas | int | `20` | The maximum number of clamav replicas |
| clamav.scaling.minReplicas | int | `2` | The minumum number of clamav replicas |
| clamav.version | string | `""` | The clamav docker image version - defaults to .Chart.appVersion |
| clamavHTTP.image | string | `"quay.io/ukhomeofficedigital/acp-clamav-http"` | The clamav-http docker image |
| clamavHTTP.resources | object | `{"limits":{"cpu":"1500m","ephemeral-storage":"1000M","memory":"3000M"},"requests":{"cpu":"1000m","ephemeral-storage":"500M","memory":"2000M"}}` | The resource requests and limits for the clamav-http service |
| clamavHTTP.version | string | `""` | The clamav-http docker image version - defaults to .Chart.appVersion |
| clamavMirror.cvdUpdate.cvdCron | string | `"*/10 * * * *"` |  |
| clamavMirror.cvdUpdate.mirrorCron | string | `"0 * * * *"` |  |
| clamavMirror.image | string | `"quay.io/ukhomeofficedigital/acp-clamav-mirror"` | The clamav-mirror docker image |
| clamavMirror.metricsPort | int | `9090` |  |
| clamavMirror.replicaCount | int | `1` |  |
| clamavMirror.resources | object | `{"limits":{"cpu":"800m","memory":"2000M"},"requests":{"cpu":"400m","memory":"1000M"}}` | The resource requests and limits for the clamav-http service |
| clamavMirror.version | string | `""` | The clamav-mirror docker image version - defaults to .Chart.appVersion |
| clamavMirror.volume.size | int | `10` |  |
| clamavMirror.volume.storageClass | string | `"gp2-encrypted"` |  |
| fullnameOverride | string | `""` | override the full name of the clamav chart |
| nameOverride | string | `""` | override the name of the clamav chart |
| nginxProxy.image | string | `"quay.io/ukhomeofficedigital/nginx-proxy"` | The nginx proxy docker image |
| nginxProxy.resources | object | `{"limits":{"cpu":"1500m","ephemeral-storage":"1000M","memory":"3000M"},"requests":{"cpu":"1000m","ephemeral-storage":"500M","memory":"2000M"}}` | The resource requests and limits for the nginx proxy service |
| nginxProxy.version | string | `"v3.4.20"` | The nginx proxy docker image version |
| service.port | int | `443` | The port to be used by the clamav service |