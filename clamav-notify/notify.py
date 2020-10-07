#!/usr/bin/env python

from kubernetes import client, config
from shutil import copyfile

import click
import sys
import time
import os
import subprocess


def sigtool(signature_file):
	"Calls sigtool and returns a dictionary of results"
	command = ["sigtool", "-i", signature_file]
	result = subprocess.check_output(command).split(b"\n")[:-2]
	return dict(line.decode('utf-8').split(": ") for line in result)


def build_annotations(versions):
	"Creates annotations object used to patch the clamav deployment"
	return {f"clamav.db.version/{key}": val for key, val in versions.items()}


def notify(namespace, deployment, versions):
	"Patches the clamav deployment with the current signature versions"
	if os.getenv('KUBERNETES_SERVICE_HOST'):
		config.load_incluster_config()
	else:
		config.load_kube_config()


	apps_v1 = client.AppsV1Api()

	api_response = apps_v1.patch_namespaced_deployment(
	    name=deployment, namespace=namespace,
	    body={"spec": {"template": {"metadata": {"annotations": build_annotations(versions)}}}}   
	)


def scan_file(definitions, filepath):
	"Scans a file using clamav"
	command = ["clamscan", "-d", definitions, filepath]
	result = subprocess.call(command)
	return result


def test_definitions(definitions):
	"Tests that clamav definitions return correct results"
	if scan_file(definitions, "files/eicar.txt") == 1:
		if scan_file(definitions, "files/safe.txt") == 0:
			return True
	return False


def copy_signature(from_location, to_location):
	"Copies a signatures to new location if it is more up to date"
	click.echo(f"Testing {to_location}")
	new_version = sigtool(from_location)['Version']
	old_version = None
	if os.path.exists(to_location) and os.path.isfile(to_location):
		old_version = sigtool(to_location)['Version']
	if old_version != new_version:
		click.echo(f"{to_location} is out of date, updating")
		copyfile(from_location, to_location)
	else:
		click.echo(f"{to_location} is up to date")
	return new_version


def copy_signatures(from_location, to_location):
	"Tests and copies signatures to a new location"
	versions = {}
	click.echo("Testing latest definitions")
	if not test_definitions(from_location):
		click.echo("New virus definitions are broken!")
		sys.exit(1)
	click.echo("Latest virus definitions are working!")
	for sigfile in os.listdir(from_location):
		if sigfile.endswith("cvd"):
			versions[sigfile] = copy_signature(
				os.path.join(from_location, sigfile),
				os.path.join(to_location, sigfile)
				)
		elif sigfile.endswith("cld"):
			# Freshhclam will replace the cvd with a cld file delete it, and freshclam will pull a cvd on the next run
			click.echo(f"Deleting unwanted cld: {sigfile}")
			os.remove(os.path.join(from_location, sigfile))
	return versions


@click.command()
@click.option('-n', '--namespace', default="default", help='The namespace of the clamav deployment')
@click.option('-d', '--deployment', default="clamav", help='The name of the clamav deployment')
@click.option('-f', '--movefrom',  required=True, help='The directory to move signatures from after testing')
@click.option('-t', '--moveto', required=True, help='The directory to move signatures to after testing')
def main(namespace, deployment, movefrom, moveto):
	versions = copy_signatures(movefrom, moveto)
	notify(namespace, deployment, versions)


if __name__ == "__main__":
	main()
