#!/bin/bash


if [ "$#" -lt 3 ]; then
	echo "Missing game_id, player_id or number"
	exit
fi


curl -X 'POST' \
  'http://bingo-api/mark-number' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d "{
  \"game_id\": \"$1\",
  \"player_id\": \"$2\",
  \"number\": $3
}"

echo ""
