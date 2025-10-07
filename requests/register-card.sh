#!/bin/bash

set -euo pipefail

if [ "$#" -lt 2  ];then
	echo "Missing player_id or numbers"
	exit
fi

player_id=$1

shift

nums=("$@")

IFS=,;car="${nums[*]}"


curl -sS -f -L\
	-X POST 'http://bingo-api/register-card' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d "{
  \"player_id\": \"$player_id\",
  \"card_numbers\": [${car[*]}]
}"
echo ""
