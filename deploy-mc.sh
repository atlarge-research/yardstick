#!/usr/bin/env bash

RUNSERVERCOMMAND="nohup ./runserver.sh > server.log 2>&1 &"

# Reserve a number of nodes.
NODES=$(./reserve-nodes $1)
# Appoint master. This will run MC Server.
MASTER=$(echo $NODES | cut -d' ' -f1)
# Appoint slaves. This will run MC clients.
SLAVES=$(echo $NODES | cut -d' ' -f2-)

# Start the MC Server.
ssh $MASTER $RUNSERVERCOMMAND
# Start the MC Clients.
for NODE in $SLAVES; do
	ssh $NODE "nohup ./runclient.sh $MASTER > slave-$NODE.log 2>&1 &"
done

# Sleep for experiment duration.
sleep $2

# Terminate all processes.
for NODE in $NODES; do
	ssh $NODE killall java
done
