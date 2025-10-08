#!/bin/bash


if [ "$#" -lt 2  ];then
	echo "Missing player_id or number"
	exit
fi

curl -X 'POST' \
  'http://bingo-api/validate-number' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d "{
  \"player_id\": \"$1\",
  \"number\": $2
}"
echo ""
