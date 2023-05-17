#!/bin/bash

# This script is used to reserve nodes on das5/das6, deploy terraria server and bot(s) and run some experiments on das5/6 nodes.

# Define the required variables
VU_SSH_HOSTNAME="ssh.data.vu.nl"
DAS5_HOSTNAME="fs0.das5.cs.vu.nl"
DAS6_HOSTNAME="fs0.das6.cs.vu.nl"

# Read the config file
. ./configs/das-config.txt

# validate the config file by checking if all the required variables are defined, NUM_NODES is a number and greater than 1 and RESERVE_DURATION is in the format HH:MM:SS
function validate_config {
    if [ -z "$VUNET_USERNAME" ] || [ -z "$IN_VU_NETWORK" ] || [ -z "$NUM_NODES" ] || [ -z "$RESERVE_DURATION" ]; then
        echo "ERROR: One or more variables from the above are not defined in das-config.txt"
        exit 1
    fi
    if [ "$DAS_VERSION_TO_USE" -eq 5 ]; then
        if [ -z "$DAS5_USERNAME" ]; then
            echo "ERROR: DAS5_USERNAME is not defined in das-config.txt"
            exit 1
        fi
    elif [ "$DAS_VERSION_TO_USE" -eq 6 ]; then
        if [ -z "$DAS6_USERNAME" ]; then
            echo "ERROR: DAS6_USERNAME is not defined in das-config.txt"
            exit 1
        fi
    else
        echo "ERROR: DAS_VERSION_TO_USE should be either 5 or 6"
        exit 1
    fi
    if ! [ "$NUM_NODES" -gt 1 ]; then
        echo "ERROR: NUM_NODES should be a number and greater than 1"
        exit 1
    fi
    if ! [[ "$RESERVE_DURATION" =~ ^[0-9][0-9]:[0-9][0-9]:[0-9][0-9]$ ]]; then
        echo "ERROR: RESERVE_DURATION should be in the format HH:MM:SS"
        exit 1
    fi
}

# ssh to das5/6 with or without proxyjump depending on whether IN_VU_NETWORK=true or not
function ssh_das {
    if [ "$DAS_VERSION_TO_USE" -eq 5 ]; then
        USERNAME=$DAS5_USERNAME
        HOSTNAME=$DAS5_HOSTNAME
    elif [ "$DAS_VERSION_TO_USE" -eq 6 ]; then
        USERNAME=$DAS6_USERNAME
        HOSTNAME=$DAS6_HOSTNAME
    fi
    if [ "$IN_VU_NETWORK" = true ] ; then
        ssh "$USERNAME@$HOSTNAME" -t "$@"
    else
        ssh -J "$VUNET_USERNAME@$VU_SSH_HOSTNAME" "$USERNAME@$HOSTNAME" -t "$@" 
    fi
}

remote_commands=$(cat <<CMD
    cd ~
    wget https://dot.net/v1/dotnet-install.sh -O dotnet-install.sh
    chmod +x dotnet-install.sh
    ./dotnet-install.sh --version latest
    echo "export DOTNET_ROOT=\$HOME/.dotnet" >> ~/.bashrc
    echo "export PATH=\$PATH:\$HOME/.dotnet:\$HOME/.dotnet/tools" >> ~/.bashrc
    source ~/.bashrc
    dir_name="terraria-experiment-$(date +%Y-%m-%d-%H-%M-%S)"
    mkdir -p "\$dir_name"
    cd "\$dir_name"
    mkdir -p server bot
    cd server
    curl -sL https://github.com/Pryaxis/TShock/releases/download/v5.1.3/TShock-5.1.3-for-Terraria-1.4.4.9-linux-x64-Release.zip -o TShock-5.1.3-for-Terraria-1.4.4.9-linux-x64-Release.zip
    unzip TShock-5.1.3-for-Terraria-1.4.4.9-linux-x64-Release.zip
    tar -xvf TShock-Beta-linux-x64-Release.tar
    rm TShock-Beta-linux-x64-Release.tar TShock-5.1.3-for-Terraria-1.4.4.9-linux-x64-Release.zip
    cd ../bot
    curl -sL https://github.com/AbhilashBalaji/Benchmarking-Terraria/releases/download/testv1/linux-x64.zip -o linux-x64.zip
    unzip linux-x64.zip
    rm linux-x64.zip
    module load prun
    preserve -llist
    echo "Reserving $NUM_NODES nodes for $RESERVE_DURATION"
    preserve -np $NUM_NODES -t $RESERVE_DURATION > reservation.txt
    cat reservation.txt | grep -o -E '[0-9]+' | head -n 1 > reservation_id.txt
    reservation_id=\$(cat reservation_id.txt) && rm reservation*.txt
    while ! preserve -llist | grep \$reservation_id | awk '{print \$7}' | grep -q "R" ;
        do
        sleep 1
        echo "Waiting for reservation to be ready"
    done
    preserve -llist | grep \$reservation_id | grep -oE 'node[0-9]+' > nodes.txt
    echo "Nodes reserved: \$(cat nodes.txt)"
    mapfile -t my_array < nodes.txt && rm nodes.txt
    server_node=\${my_array[0]}
    echo "Server node: \$server_node"
    bot_nodes=\${my_array[@]:1}
    echo "Bot nodes: \$bot_nodes"
    ssh \$server_node 'dotnet --version'
CMD
)

validate_config
ssh_das "$remote_commands"
