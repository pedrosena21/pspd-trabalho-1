#!/bin/bash 

if [ "$#" -lt 1  ];then
	echo "Missing player_id"
	exit
fi

curl -sS -f -L\
	-X POST 'http://bingo-api/get-card' \
  	-H 'accept: application/json' \
  	-H 'Content-Type: application/json' \
  	-d "{
  \"player_id\": \"$1\"
}"
echo ""
