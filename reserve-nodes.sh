!#/usr/bin/env bash

module load prun

preserve -np $1 -t 15:00
NODES=$(preserve -long-list | grep $(whoami) | cut -d'	' -f9)
echo $NODES
