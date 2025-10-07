#!/bin/bash

if [ "$#" -lt 2 ]; then
	echo "Missing game_id or player_name"
	exit
fi


curl -sS -f -L \
	-X POST 'http://bingo-api/register-player' \
  	-H 'accept: application/json' \
  	-H 'Content-Type: application/json' \
  	-d "{\"game_id\": \"$1\",\"player_name\": \"$2\" }"
echo ""
