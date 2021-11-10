#!/usr/bin/env sh

BENCHMARKMC=$1
DASTOOLS=$2

PATH=$PATH:$BENCHMARKING
PATH=$PATH:$DASTOOLS

chown +x $BENCHMARKING/*.py
chown +x $DASTOOLS/*.py

EXPNAME=test

ereserve.py start --monitor $EXPNAME 1:server 1:client
for node in $(ereserve.py list $EXPNAME); do
	ssh ${node}.ib.cluster "$BENCHMARKING/setup/start.sh > /dev/null 2> /dev/null < /dev/null &"

