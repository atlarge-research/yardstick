#!/bin/bash
cargo build --release

curl -s servers.minetest.net/list.json \
	| jq -r '.list[] | .address + ":" + (.port|tostring)' \
	| xargs -n 1 ./target/release/texmodbot -q 5 -Q \
	| (trap '' INT; grep '[\[\^]' | tee /tmp/texmods.txt)

echo "scraped texmods saved to /tmp/texmods.txt"
