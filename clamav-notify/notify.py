import sys, time, os, subprocess
import click

from shutil import copytree, rmtree

from kubernetes import client, config


def notify(namespace, deployment):
	if os.getenv('KUBERNETES_SERVICE_HOST'):
		config.load_incluster_config()
	else:
		config.load_kube_config()


	apps_v1 = client.AppsV1Api()

	api_response = apps_v1.patch_namespaced_deployment(
	    name=deployment, namespace=namespace,
	    body={"spec": {"template": {"metadata": {"annotations": {"clamavSignatureUpdateTime": str(time.time())}}}}}   
	)


def scan_file(definitions, filepath):
	command = ["clamscan", "-d", definitions, filepath]
	result = subprocess.call(command)
	return result


def test_definitions(definitions):
	if scan_file(definitions, "files/eicar.txt") == 1:
		if scan_file(definitions, "files/safe.txt") == 0:
			return True
	return False


def copy_signatures(from_location, to_location):
	rmtree(to_location)
	copytree(from_location, to_location)


@click.command()
@click.option('-n', '--namespace', default="default", help='The namespace of the clamav deployment')
@click.option('-d', '--deployment', default="clamav", help='The name of the clamav deployment')
@click.option('--test', is_flag=True, help='Should we test the virus definitions')
@click.option('-f', '--movefrom', default="", help='The directory to move signatures from after testing')
@click.option('-t', '--moveto', default="", help='The directory to move signatures to after testing')
def main(namespace, deployment, test, movefrom, moveto):
	if test:
		if test_definitions(movefrom):
			copy_signatures(movefrom, moveto)
		else:
			sys.exit(1)
	notify(namespace, deployment)


if __name__ == "__main__":
	main()