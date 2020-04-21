import sys, time, os
from kubernetes import client, config


if os.getenv('KUBERNETES_SERVICE_HOST'):
	config.load_incluster_config()
else:
	config.load_kube_config()


apps_v1 = client.AppsV1Api()

if len(sys.argv) < 3:
	sys.exit()

api_response = apps_v1.patch_namespaced_deployment(
    name=sys.argv[2], namespace=sys.argv[1],
    body={"spec": {"template": {"metadata": {"annotations": {"clamavSignatureUpdateTime": str(time.time())}}}}}   
)