#!/usr/bin/env bash

RUNSERVERCOMMAND="nohup ./runserver.sh > server.log 2>&1 &"

# Reserve a number of nodes.
module load prun
preserve -np $! -t 15:00
sleep 2
NODES=$(preserve -long-list | grep $(whoami) | cut -d'	' -f9)
# Appoint master. This will run MC Server.
MASTER=$(echo $NODES | cut -d' ' -f1)
# Appoint slaves. This will run MC clients.
SLAVES=$(echo $NODES | cut -d' ' -f2-)

# Start the MC Server.
echo "Starting server on $MASTER"
ssh $MASTER $RUNSERVERCOMMAND
# Start the MC Clients.
for NODE in $SLAVES; do
	echo "Starting client on $NODE"
	ssh $NODE "nohup ./runclient.sh $MASTER > slave-$NODE.log 2>&1 &"
done

# Sleep for experiment duration.
echo "Experiment is running. Waiting $2 seconds."
sleep $2

# Terminate all processes.
for NODE in $NODES; do
	ssh $NODE killall java
done
