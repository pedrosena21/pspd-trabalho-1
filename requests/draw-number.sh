#!/bin/bash

if [ "$#" -lt 1 ];then
	echo "Missing game_id"
	exit
fi

curl -sS -f -L \
	-X POST 'http://bingo-api/draw-number' \
	-H 'accept: */*' \
 	-H 'Content-Type: application/json' \
  	-d "{\"game_id\": \"$1\"}"

echo ""

