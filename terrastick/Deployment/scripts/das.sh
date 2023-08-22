#!/bin/bash

# This script is used to reserve nodes on das5/das6, deploy terraria server and bot(s) and run some experiments on das5/6 nodes.

# Read the config file
. ./configs/das-config.txt

EXP_TIME=$(date +%Y-%m-%d-%H-%M-%S)
DIR_NAME="/var/scratch/$VUNET_USERNAME/terraria-experiment-$EXP_TIME"

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




remote_commands=$(cat <<CMD
    TERRASTICK_VERSION=$TERRASTICK_VERSION
    TERRASTICK_WORKLOAD=$TERRASTICK_WORKLOAD
    TERRASTICK_IP=$TERRASTICK_IP
    PROMETHEUS_IP=$PROMETHEUS_IP
    TERRASTICK_WORKLOAD_DURATION=$TERRASTICK_WORKLOAD_DURATION
    TERRASTICK_TILING=$TERRASTICK_TILING
    DIR_NAME=$DIR_NAME
    DOTNET_ROOT=\$HOME/.dotnet
    PATH=\$PATH:\$HOME/.dotnet:\$HOME/.dotnet/tools
    variable_list=("TERRASTICK_WORKLOAD" "TERRASTICK_IP" "DOTNET_ROOT" "PATH" "TERRASTICK_VERSION" "TERRASTICK_WORKLOAD_DURATION" "DIR_NAME" "TERRASTICK_TILING" "PROMETHEUS_IP")
    for variable_name in "\${variable_list[@]}"; do
        variable_value="\${!variable_name}"
        if ! grep -q "^export \$variable_name=" ~/.bashrc; then
            echo "export \$variable_name=\"\$variable_value\"" >> ~/.bashrc
            echo "Added the variable \$variable_name to the bash RC file."
        else
            # Variable is already set, update it to its latest value using sed
            sed -i "s|^export \$variable_name=.*|export \$variable_name=\"\$variable_value\"|" ~/.bashrc
            echo "Updated the variable \$variable_name in the bash RC file."
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
    mkdir -p server bot prometheus plots
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
    wget https://github.com/prometheus/node_exporter/releases/download/v1.6.0/node_exporter-1.6.0.linux-amd64.tar.gz
    tar -xvf node_exporter-1.6.0.linux-amd64.tar.gz && rm node_exporter-1.6.0.linux-amd64.tar.gz
    cd ServerPlugins
    # curl -sL https://github.com/thanatos-tshock/Tiled/releases/download/v2.0.0.0/Tiled.dll -o Tiled.dll
    curl -sL https://github.com/atlarge-research/yardstick/releases/download/$TERRASTICK_VERSION/server-side-packet-monitor.zip -o server-side-packet-monitor.zip
    unzip -n server-side-packet-monitor.zip && rm server-side-packet-monitor.zip
    cd ../../bot
    curl -sL https://github.com/atlarge-research/yardstick/archive/refs/tags/$TERRASTICK_VERSION.zip -o terrastick.zip
    unzip terrastick.zip && rm terrastick.zip
    mv yardstick-$TERRASTICK_VERSION/terrastick/Deployment/worlds ../server/
    mv yardstick-$TERRASTICK_VERSION/terrastick/Deployment/metrics-configs/prometheus-terrastick.yml ../prometheus/prometheus-2.37.8.linux-amd64/
    mv yardstick-$TERRASTICK_VERSION/terrastick/Deployment/metrics-configs/server-process-exporter.yaml ../server/process-exporter-0.7.10.linux-amd64/
    mkdir -p ~/temp && cp yardstick-$TERRASTICK_VERSION/terrastick/analysisScripts/* ~/temp/ # hacky workaround to run analysis on the server node, otherwise the long path creates problems

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
    sed -i "s/export PROMETHEUS_IP=.*/export PROMETHEUS_IP=10.141.0.\$(echo \$prometheus_node | sed 's/node0*\([1-9][0-9]*\)/\1/' | grep -oE '[0-9]+')/" ~/.bashrc
    source ~/.bashrc

    if [ "$TERRASTICK_TILING" == "VANILLA" ]; then
        ssh \$server_node 'cd $DIR_NAME/server && screen -L -S server -d -m bash -c "./TShock.Server -port 7777 -maxplayers 200 -world $DIR_NAME/server/worlds/$WORLD_NAME.wld "' && echo "Server started on \$server_node"
    elif [ "$TERRASTICK_TILING" == "HEAPTILE" ]; then
        ssh \$server_node 'cd $DIR_NAME/server && screen -L -S server -d -m bash -c "./TShock.Server -port 7777 -heaptile -maxplayers 200 -world $DIR_NAME/server/worlds/$WORLD_NAME.wld "' && echo "Server started on \$server_node"
    elif [ "$TERRASTICK_TILING" == "CONSTILEATION" ]; then
        ssh \$server_node 'cd $DIR_NAME/server && screen -L -S server -d -m bash -c "./TShock.Server -port 7777 -constileation -maxplayers 200 -world $DIR_NAME/server/worlds/$WORLD_NAME.wld "' && echo "Server started on \$server_node"
    fi
    echo "waiting for server to start" && sleep 10

    # start node and process exporter on server node
    ssh \$server_node 'cd $DIR_NAME/server/process-exporter-0.7.10.linux-amd64 && screen -L -S process-exporter -d -m bash -c "./process-exporter -config.path server-process-exporter.yaml -web.listen-address \$TERRASTICK_IP:9256"' && echo "Process exporter started on \$server_node"
    ssh \$server_node 'cd $DIR_NAME/server/node_exporter-1.6.0.linux-amd64 && screen -L -S node-exporter -d -m bash -c "./node_exporter"' && echo "Node exporter started on \$server_node"
    
    sed -i "s/TERRASTICK_IP/\$TERRASTICK_IP/g" $DIR_NAME/prometheus/prometheus-2.37.8.linux-amd64/prometheus-terrastick.yml
    ssh \$prometheus_node 'cd $DIR_NAME/prometheus/prometheus-2.37.8.linux-amd64 && screen -L -S prometheus -d -m bash -c "./prometheus --config.file=prometheus-terrastick.yml"' && echo "Prometheus started on \$prometheus_node"
    echo "waiting for prometheus to start and waiting for server to load up" && sleep 30
    
    echo "Running workload with $TERRASTICK_WORKLOAD ...."

    total_wait_time=0
    start_timestamp=$(date +%s)
    echo "START=\$start_timestamp" > $DIR_NAME/exp_times.txt
    for node in \$bot_nodes; do
        echo "Bot node: \$node"
        for i in {1..$NUM_BOTS_PER_NODE}; do
            ssh \$node 'cd $DIR_NAME/bot/yardstick-$TERRASTICK_VERSION/terrastick/PlayerEmulations/TrClientTest/bin/Release/net6.0/linux-x64/ && screen -L -S bot-\$node -d -m bash -c "./TrClientTest"' & 
            # wait for WAIT_TIME_BETWEEN_BOTS 
            sleep $WAIT_TIME_BETWEEN_BOTS
            total_wait_time=$((total_wait_time + WAIT_TIME_BETWEEN_BOTS))
        done


        echo "Bot started on \$node"
    done

    sleep $((TERRASTICK_WORKLOAD_DURATION - total_wait_time))

    end_timestamp=$(date +%s)
    echo "END=\$end_timestamp" >> $DIR_NAME/exp_times.txt
    echo "Workload finished"

    # kill all the processes
    for node in \$bot_nodes; do
        ssh \$node 'screen -S bot-\$node -X quit' && echo "Bot stopped on \$node"
    done
    ssh \$server_node 'screen -S server -X quit' && echo "Server stopped"
    ssh \$server_node 'screen -S process-exporter -X quit' && echo "Process exporter stopped"

    # get prometheus logs by running the get_prometheus_logs.sh script
    ssh \$prometheus_node 'cd ~/temp/ && ./get_prometheus_logs.sh || echo "failed to get prometheus logs"'

    # run analysis scipts
    ssh \$server_node 'module load python/3.6.0'
    ssh \$server_node 'cd ~/temp/ && ./run_analysis.sh' && echo "Analysis done"
CMD
)


validate_config
ssh_das "$remote_commands"
