clamav
======
A Helm chart for deploying a clamav-http service on kubernetes

Current chart version is `0.2.4`





## Chart Values

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| clamav.certificate.create | bool | `true` | Should a certificate be created for the clamav service |
| clamav.certificate.issuer | object | `{"kind":"ClusterIssuer","name":"platform-ca"}` | The issuer to use when creating a certificate |
| clamav.certificate.secretName | string | `""` | Override the default certificate secret name |
| clamav.freshclam.mirrors | list | `["db.uk.clamav.net","database.clamav.net"]` | A list of clamav mirrors to be used by the clamav service |
| clamav.image | string | `"quay.io/ukhomeofficedigital/acp-clamav"` | The clamav docker image |
| clamav.limits.fileSize | int | `20` | The largest file size scanable by clamav, in MB |
| clamav.limits.scanSize | int | `100` | The largest scan size permitted in clamav, in MB |
| clamav.resources | object | `{"limits":{"cpu":"1500m","ephemeral-storage":"1000M","memory":"3000M"},"requests":{"cpu":"1000m","ephemeral-storage":"500M","memory":"2000M"}}` | The resource requests and limits for the clamav service |
| clamav.scaling.cpuTarget | int | `30` | The target cpu usage percentage for clamav |
| clamav.scaling.maxReplicas | int | `20` | The maximum number of clamav replicas |
| clamav.scaling.memoryTarget | int | `30` | The target memory usage percentage for clamav |
| clamav.scaling.minReplicas | int | `2` | The minumum number of clamav replicas |
| clamav.version | string | `""` | The clamav docker image version - defaults to .Chart.appVersion |
| clamavHTTP.image | string | `"quay.io/ukhomeofficedigital/acp-clamav-http"` | The clamav-http docker image |
| clamavHTTP.resources | object | `{"limits":{"cpu":"1500m","ephemeral-storage":"1000M","memory":"3000M"},"requests":{"cpu":"1000m","ephemeral-storage":"500M","memory":"2000M"}}` | The resource requests and limits for the clamav-http service |
| clamavHTTP.version | string | `""` | The clamav-http docker image version - defaults to .Chart.appVersion |
| clamavNotify.freshclam.checkFrequency | int | `24` | The number of checks for new virus definitions per day |
| clamavNotify.freshclam.mirrors | list | `["db.uk.clamav.net","database.clamav.net"]` | A list of clamav mirrors to be used by the clamav-notify service |
| clamavNotify.image | string | `"quay.io/ukhomeofficedigital/acp-clamav-notify"` | The clamav-notify docker image |
| clamavNotify.resources | object | `{"limits":{"cpu":"800m","memory":"2000M"},"requests":{"cpu":"400m","memory":"1000M"}}` | The resource requests and limits for the clamav-http service |
| clamavNotify.version | string | `""` | The clamav-notify-cron docker image version - defaults to .Chart.appVersion |
| clamavNotify.volume.size | int | `5` | The size class of the volume used by clamav-notify in GB |
| clamavNotify.volume.storageClass | string | `"gp2-encrypted"` | The storage class of the volume used by clamav-notify |
| clamavNotifyCron.image | string | `"quay.io/ukhomeofficedigital/acp-clamav-notify-cron"` | The clamav-notify-cron docker image |
| clamavNotifyCron.schedule | string | `"*/15 * * * *"` | The cron schedule for loading updated signatures |
| clamavNotifyCron.version | string | `""` |  |
| fullnameOverride | string | `""` | override the full name of the clamav chart |
| nameOverride | string | `""` | override the name of the clamav chart |
| nginxProxy.image | string | `"quay.io/ukhomeofficedigital/nginx-proxy"` | The nginx proxy docker image |
| nginxProxy.resources | object | `{"limits":{"cpu":"1500m","ephemeral-storage":"1000M","memory":"3000M"},"requests":{"cpu":"1000m","ephemeral-storage":"500M","memory":"2000M"}}` | The resource requests and limits for the nginx proxy service |
| nginxProxy.version | string | `"v3.4.20"` | The nginx proxy docker image version |
| service.ingress | list | `[{"podSelector":{}}]` | Specifies ingress rules for the clamav service |
| service.port | int | `443` | The port to be used by the clamav service |
| serviceAccount.annotations | object | `{}` | Annotaions for the service account used by clamav-notify |
| serviceAccount.create | bool | `true` | Should we create the service account and roles |
| serviceAccount.name | string | `"clamav-notify"` | The name of the service account used by clamav-notify |
