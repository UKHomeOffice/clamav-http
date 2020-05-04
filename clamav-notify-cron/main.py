#!/usr/bin/env python

import os

from kubernetes import client, config
from kubernetes.stream import stream


if os.getenv('KUBERNETES_SERVICE_HOST'):
    config.load_incluster_config()
else:
    config.load_kube_config()


api = client.CoreV1Api()

label_selector = 'name=clamav-notify'
namespace = 'clamav'

pods = api.list_namespaced_pod(namespace=namespace, label_selector=label_selector).items


for pod in pods:
    name = pod.metadata.name

    exec_command = [
      "python", "/clam/notify.py",
      "-f", "/var/lib/clamav",
      "-t", "/var/lib/clamav/mirror",
      "-n", "clamav", "-d", "clamav"
    ]

    response = stream(api.connect_get_namespaced_pod_exec, name, namespace,
              command=exec_command, stderr=True, stdin=False, stdout=True, tty=False)

    print(response)