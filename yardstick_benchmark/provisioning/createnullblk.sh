#!/bin/bash

# This script is adapted from the Zoned Storage Documentation at 

if [ $# != 3 ]; then
    echo "Usage: $0 <sect size (B)> <total size (MB)> <latency (ns)>"
    exit 1
fi

scriptdir=$(cd $(dirname "$0") && pwd)

modprobe null_blk nr_devices=0 || return $?

function create_nullb()
{
    local nid=0
    local bs=$1
    local cap=$2
    local completion_nsec=$3

    while [ 1 ]; do
        if [ ! -b "/dev/nullb$nid" ]; then
            break
        fi
        nid=$(( nid + 1 ))
    done

    dev="/sys/kernel/config/nullb/nullb$nid"
    mkdir "$dev"

    echo $bs > "$dev"/blocksize
    echo $completion_nsec > "$dev"/completion_nsec
    echo 2 > "$dev"/irqmode
    echo 2 > "$dev"/queue_mode
    echo 1024 > "$dev"/hw_queue_depth
    echo 1 > "$dev"/memory_backed
    echo 0 > "$dev"/zoned

    echo $cap > "$dev"/size

    echo 1 > "$dev"/power

    echo "$nid"
}

nulldev=$(create_nullb $1 $2 $3)
echo "nullb$nulldev"