#!/usr/bin/env python

import time

from kubernetes import config
from kubernetes.client import Configuration
from kubernetes.client.apis import core_v1_api
from kubernetes.client.rest import ApiException
from kubernetes.stream import stream


if os.getenv('KUBERNETES_SERVICE_HOST'):
    config.load_incluster_config()
else:
    config.load_kube_config()


api = core_v1_api.CoreV1Api()

label_selector = 'name=clamav-notify'
namespace = 'clamav'

resp = api.list_namespaced_pod(namespace=namespace, label_selector=label_selector)

for x in resp.items:
    resp = api.read_namespaced_pod(name=name, namespace=namespace)

    exec_command = [
    '/bin/sh',
    '-c',
    'opt/zookeeper/bin/zkCleanup.sh -n 10'
    ]

    resp = stream(api.connect_get_namespaced_pod_exec, name, namespace,
              command=exec_command, stderr=True, stdin=False, stdout=True, tty=False)

  print(resp)