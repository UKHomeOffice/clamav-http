#!/bin/sh

curl -s -F "name=eicar" -F "file=@test/safe.txt" "$1/scan" | grep -q "Everything ok : true"
