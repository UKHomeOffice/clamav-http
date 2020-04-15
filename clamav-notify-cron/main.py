#!/usr/bin/env python

import os
import click

from kubernetes import client, config
from kubernetes.stream import stream


@click.command()
@click.option('-n', '--namespace', default="default", help='The namespace of the clamav deployment')
@click.option('-d', '--deployment', default="clamav", help='The name of the clamav deployment')
@click.option('-p', '--pod', default="clamav-notify", help='The name of the clamav-notify deployment')
def main(namespace, deployment, pod ):
    if os.getenv('KUBERNETES_SERVICE_HOST'):
        config.load_incluster_config()
    else:
        config.load_kube_config()


    api = client.CoreV1Api()

    pods = api.list_namespaced_pod(namespace=namespace, label_selector=f"name={pod}").items


    for pod in pods:
        name = pod.metadata.name

        exec_command = [
            "python", "/clam/notify.py",
            "-f", "/var/lib/clamav",
            "-t", "/var/lib/clamav/mirror",
            "-n", namespace, "-d", deployment
        ]

        response = stream(api.connect_get_namespaced_pod_exec, name, namespace,
                command=exec_command, stderr=True, stdin=False, stdout=True, tty=False)

        click.echo(response)

if __name__ == "__main__":
    main()