#!/bin/bash

failures=0


DOCKER_IP="${DOCKER_IP:-127.0.0.1}"
CLAMAV_HTTP_ENDPOINT=http://$DOCKER_IP:8080

#docker-compose -f test/docker-compose.yml build

docker-compose -f test/docker-compose.yml up --build -d


echo "Waiting for clamd service"
n=0
until [ $n -ge 60 ]
do
  curl -s "$CLAMAV_HTTP_ENDPOINT" | grep -q 'Clamd responding: true'  && break
  n=$[$n+1]
  sleep 10
done


if [ $n -ge 60 ]
then
  failures=1
  echo "Clamav failed to start"
else
  echo "Clamav is running"
  for f in test/tests/*.sh
  do
    $f $CLAMAV_HTTP_ENDPOINT
    if [ $? -ne 0 ]; then
      echo "$f: Failed"
      failures=$[$failures+1]
    else
      echo "$f: Success"
	fi
  done
  echo "Tests complete with $failures failures"
fi

#docker-compose -f test/docker-compose.yml down

exit $failures
