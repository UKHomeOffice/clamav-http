#!/bin/sh

curl -s -F "name=eicar" -F "file=@test/eicar.txt" "$1/scan" | grep -q "Everything ok : false"
