#!/bin/sh


docker login -u="ukhomeofficedigital+acp_clamav" -p=${DOCKER_PASSWORD} quay.io

for image in 'clamav' 'clamav-http' 'clamav-notify' 'clamav-notify-cron'
do
  docker build --no-cache -t "quay.io/ukhomeofficedigital/acp-$image:$DRONE_COMMIT_SHA" "$image"
  for tag in "$@"
  do
    docker tag "quay.io/ukhomeofficedigital/acp-$image:$DRONE_COMMIT_SHA" "quay.io/ukhomeofficedigital/acp-$image:$tag"
    docker push "quay.io/ukhomeofficedigital/acp-$image:$tag"
  done
done
