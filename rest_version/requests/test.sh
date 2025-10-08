#!/bin/bash

set -euo pipefail

GAME="bingo"
PLAYER="Leo"

create_game_json="$(./create-game.sh "$GAME")"
game_id="$(jq -r '.game_id' <<<"$create_game_json")"
echo "Game created"

register_player_json="$(./register-player.sh "$game_id" "$PLAYER")"
player_id="$(jq -r '.player_id' <<<"$register_player_json")"
card_numbers="$(jq -r '.card_numbers' <<<"$register_player_json")"
echo "Player registered"

draw_number_json="$(./draw-number.sh "$game_id")"
number="$(jq -r '.number' <<<"$draw_number_json")"
echo "Number: $number"

nums=(1 2 3)
echo "Numbers: ${nums[*]}"
register_card_json="$(./register-card.sh "$player_id" "${nums[@]}")"

get_card_json="$(./get-card.sh "$player_id")"
card_numbers="$(jq -r '.card_numbers' <<<"$get_card_json")"
echo "Card = $card_numbers"

