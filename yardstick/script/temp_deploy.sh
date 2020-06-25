#!/usr/bin/env bash

NUMBEROFNODES=$1
RUNTIME=$2
CONFIG=$3
RUNSERVERCOMMAND="nohup ./runserver.sh $CONFIG > server.log 2>&1 &"

for NUMBEROFPLAYERS in {0..50..5}; do

    # Reserve a number of nodes.
    module load prun
    JOBID=$(preserve -np $NUMBEROFNODES -t 20:00 | grep -oE '[0-9]*')
    sleep 5
    NODES=$(preserve -long-list | grep $(whoami) | grep $JOBID | cut -d$'\t' -f9)
    # Appoint master. This will run MC Server.
    MASTER=$(echo $NODES | cut -d' ' -f1)
    # Appoint slaves. This will run MC clients.
    SLAVES=$(echo $NODES | cut -d' ' -f2-)

    echo "Running with nodes: $NODES with job id $JOBID"

    # Start the MC Server.
    echo "Starting server on $MASTER"
    ssh $MASTER $RUNSERVERCOMMAND

    sleep 20
    # Start the MC Clients.
    for NODE in $SLAVES; do
        echo "Starting client on $NODE"
        sleep 5
        ssh $NODE "nohup ./runclient.sh $MASTER $NUMBEROFPLAYERS > slave-$NODE-$NUMBEROFPLAYERS.log 2>&1 &"
    done

    # Sleep for experiment duration.
    echo "Experiment is running. Waiting $RUNTIME seconds."
    sleep $RUNTIME

    # Terminate all processes.
    for NODE in $NODES; do
        ssh $NODE killall java
    done

    scancel $JOBID
    rm -rf worlds

done
