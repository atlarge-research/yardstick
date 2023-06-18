#!/bin/bash

# This script is used to reserve nodes on das5/das6, deploy terraria server and bot(s) and run some experiments on das5/6 nodes.

# Define the required variables
EXP_TIME=$(date +%Y-%m-%d-%H-%M-%S)
DIR_NAME="terraria-experiment-$EXP_TIME"
VU_SSH_HOSTNAME="ssh.data.vu.nl"
DAS5_HOSTNAME="fs0.das5.cs.vu.nl"
DAS6_HOSTNAME="fs0.das6.cs.vu.nl"

# Read the config file
. ./configs/das-config.txt

# validate the config file by checking if all the required variables are defined, NUM_NODES is a number and greater than 1 and RESERVE_DURATION is in the format HH:MM:SS
function validate_config {
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

# ssh to das5/6 and execute the commands
function ssh_das {
    if [ "$DAS_VERSION_TO_USE" -eq 5 ]; then
        USERNAME=$DAS5_USERNAME
        HOSTNAME=$DAS5_HOSTNAME
    elif [ "$DAS_VERSION_TO_USE" -eq 6 ]; then
        USERNAME=$DAS6_USERNAME
        HOSTNAME=$DAS6_HOSTNAME
    fi
    ssh -J "$VUNET_USERNAME@$VU_SSH_HOSTNAME" "$USERNAME@$HOSTNAME" -t "$@" 
}

# scp files/directory to das5/6
function scp_das {
    # Arguments
    local TRANSFER_MODE=$1
    local FROM_PATH=$2
    local TO_PATH=$3

    # Destination server details
    if [ "$DAS_VERSION_TO_USE" -eq 5 ]; then
        USERNAME=$DAS5_USERNAME
        HOSTNAME=$DAS5_HOSTNAME
    elif [ "$DAS_VERSION_TO_USE" -eq 6 ]; then
        USERNAME=$DAS6_USERNAME
        HOSTNAME=$DAS6_HOSTNAME
    fi

    # Check transfer mode and perform the respective scp command
    if [ "$TRANSFER_MODE" = "file" ]; then
        scp -o ProxyJump=${VUNET_USERNAME}@${VU_SSH_HOSTNAME} ${FROM_PATH} ${USERNAME}@${HOSTNAME}:${TO_PATH}
    elif [ "$TRANSFER_MODE" = "folder" ]; then
        scp -r -o ProxyJump=${VUNET_USERNAME}@${VU_SSH_HOSTNAME} ${FROM_PATH} ${USERNAME}@${HOSTNAME}:${TO_PATH}
    else
        echo "Invalid transfer mode. Please use 'file' or 'folder'."
    fi
}

remote_commands=$(cat <<CMD
    TERRASTICK_WORKLOAD=$TERRASTICK_WORKLOAD
    TERRASTICK_IP=$TERRASTICK_IP
    DOTNET_ROOT=\$HOME/.dotnet
    PATH=\$PATH:\$HOME/.dotnet:\$HOME/.dotnet/tools
    variable_list=("TERRASTICK_WORKLOAD" "TERRASTICK_IP" "DOTNET_ROOT" "PATH")
    for variable_name in "\${variable_list[@]}"; do
        variable_value="\${!variable_name}"
        if ! grep -q "^export \$variable_name=" ~/.bashrc; then
            echo "export \$variable_name=\"\$variable_value\"" >> ~/.bashrc
            echo "Added the variable \$variable_name to the bash RC file."
        else
            # Variable is already set
            echo "The variable \$variable_name is already set in the bash RC file."
        fi
    done
    cd ~
    if ! [ -f dotnet-install.sh ]; then
        wget https://dot.net/v1/dotnet-install.sh -O dotnet-install.sh
        chmod +x dotnet-install.sh
    fi
    ./dotnet-install.sh --version latest
    source ~/.bashrc
    dir_name="$DIR_NAME"
    mkdir -p "\$dir_name"
    cd "\$dir_name"
    mkdir -p server bot prometheus
    cd prometheus
    curl -sL  https://github.com/prometheus/prometheus/releases/download/v2.37.8/prometheus-2.37.8.linux-amd64.tar.gz -o prometheus.gz
    tar -xvf prometheus.gz && rm prometheus.gz
    cd ../server
    curl -sL https://github.com/Pryaxis/TShock/releases/download/v5.1.3/TShock-5.1.3-for-Terraria-1.4.4.9-linux-x64-Release.zip -o TShock-5.1.3-for-Terraria-1.4.4.9-linux-x64-Release.zip
    unzip TShock-5.1.3-for-Terraria-1.4.4.9-linux-x64-Release.zip
    tar -xvf TShock-Beta-linux-x64-Release.tar
    rm TShock-Beta-linux-x64-Release.tar TShock-5.1.3-for-Terraria-1.4.4.9-linux-x64-Release.zip
    curl -sL https://github.com/ncabatoff/process-exporter/releases/download/v0.7.10/process-exporter-0.7.10.linux-amd64.tar.gz -o process-exporter.gz
    tar -xvf process-exporter.gz && rm process-exporter.gz
    cd ServerPlugins
    curl -sL https://github.com/atlarge-research/yardstick/releases/download/$TERRASTICK_VERSION/server-side-packet-monitor.zip -o server-side-packet-monitor.zip
    unzip -n server-side-packet-monitor.zip && rm server-side-packet-monitor.zip
    cd ../../bot
    curl -sL https://github.com/atlarge-research/yardstick/archive/refs/tags/$TERRASTICK_VERSION.zip -o terrastick.zip
    unzip terrastick.zip && rm terrastick.zip
    mv yardstick-$TERRASTICK_VERSION/terrastick/Deployment/worlds ../server/
    mv yardstick-$TERRASTICK_VERSION/terrastick/Deployment/metrics-configs/prometheus-terrastick.yml ../prometheus/prometheus-2.37.8.linux-amd64/
    mv yardstick-$TERRASTICK_VERSION/terrastick/Deployment/metrics-configs/server-process-exporter.yaml ../server/process-exporter-0.7.10.linux-amd64/
    cd yardstick-$TERRASTICK_VERSION/terrastick/PlayerEmulations/TrClientTest && dotnet build -r linux-x64 -c Release --no-self-contained || echo "Build failed"
    module load prun
    preserve -llist
    echo "Reserving $NUM_NODES nodes for $RESERVE_DURATION. Out of the nodes reserved, one will be used as the server node, one as the prometheus node, and the rest as bot nodes."
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
    # bot nodes are all nodes except the first one and last one
    bot_nodes=\${my_array[@]:1:\${#my_array[@]}-2}
    echo "Bot nodes: \$bot_nodes"
    prometheus_node=\${my_array[-1]}
    echo "Prometheus node: \$prometheus_node"

    
    sed -i "s/export TERRASTICK_IP=.*/export TERRASTICK_IP=10.141.0.\$(echo \$server_node | sed 's/node0*\([1-9][0-9]*\)/\1/' | grep -oE '[0-9]+')/" ~/.bashrc
    sed -i 's/export TERRASTICK_WORKLOAD=.*/export TERRASTICK_WORKLOAD=TEL/' ~/.bashrc
    source ~/.bashrc
    ssh \$server_node 'cd ~/$DIR_NAME/server && screen -L -S server -d -m bash -c "./TShock.Server -world ~/$DIR_NAME/server/worlds/$WORLD_NAME.wld"' && echo "Server started on \$server_node"
    echo "waiting for server to start" && sleep 10

    # start process exporter on server node
    ssh \$server_node 'cd ~/$DIR_NAME/server/process-exporter-0.7.10.linux-amd64 && screen -L -S process-exporter -d -m bash -c "./process-exporter -config.path server-process-exporter.yaml -web.listen-address \$TERRASTICK_IP:9256"' && echo "Process exporter started on \$server_node"
    
    # start prometheus on prometheus node
    sed -i "s/TERRASTICK_IP/\$TERRASTICK_IP/g" ~/$DIR_NAME/prometheus/prometheus-2.37.8.linux-amd64/prometheus-terrastick.yml
    ssh \$prometheus_node 'cd ~/$DIR_NAME/prometheus/prometheus-2.37.8.linux-amd64 && screen -L -S prometheus -d -m bash -c "./prometheus --config.file=prometheus-terrastick.yml"' && echo "Prometheus started on \$prometheus_node"
    # echo "waiting for prometheus to start" && sleep 10
    
    for node in \$bot_nodes; do
        echo "Bot node: \$node"
        ssh \$node 'cd ~/$DIR_NAME/bot/yardstick-$TERRASTICK_VERSION/terrastick/PlayerEmulations/TrClientTest/bin/Release/net6.0/linux-x64/ && screen -L -S bot-\$node -d -m bash -c "./TrClientTest"'
        echo "Bot started on \$node"
    done
    echo "Server and bots started"
CMD
)


validate_config
ssh_das "$remote_commands"
