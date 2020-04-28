#!/bin/sh

curl -s -F "name=eicar" -F "file=@test/safe.txt" "$1/v2alpha/scan" -o /dev/null -w "%{http_code}" | grep -q "200"
