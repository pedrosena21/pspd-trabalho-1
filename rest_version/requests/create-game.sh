#!/bin/bash

set -euo pipefail

if [ "$#" -lt 1 ]; then
	echo "Missing name"
	exit
fi

curl -sS -f -L \
	-X POST 'http://bingo-api/create-game' \
  	-H 'accept: */*' \
  	-H 'Content-Type: application/json' \
  	-d "{\"game_name\": \"$1\"}"

echo

