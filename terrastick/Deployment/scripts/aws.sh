## This script has been tested only a few times and may not work as expected.
## Please use it as a reference and modify it as needed.

#!/bin/bash

# Define the required variables
EXP_TIME=$(date +%Y-%m-%d-%H-%M-%S)
DIR_NAME="terraria-experiment-$EXP_TIME"

# load the config file 
. ./configs/aws-config.txt

export AWS_ACCESS_KEY_ID=$ACCESS_KEY_ID
export AWS_SECRET_ACCESS_KEY=$SECRET_ACCESS_KEY
export AWS_DEFAULT_PROFILE=$PROFILE_NAME

# Define the required variables
AWS_REGION=$REGION
KEY_PAIR_NAME="terrariaaws"
SECURITY_GROUP_NAME="terraria"
INSTANCE_TYPE=$INSTANCE_TYPE
AMI_ID=$BASE_AMI_ID
NUM_BOT_INSTANCES=$NUM_BOT_INSTANCES

# Function to create key pair
create_key_pair() {
  local key_pair_name=$1
  local region=$2

  local key_pair_exists=$(aws ec2 describe-key-pairs \
    --region "$region" \
    --filters "Name=key-name,Values=$key_pair_name" \
    --query 'KeyPairs[0].KeyName' \
    --output text)

  if [ "$key_pair_exists" == "None" ]; then
    echo "Creating a temp folder..."
    mkdir -p temp
    echo "Creating new key pair: $key_pair_name..."
    aws ec2 create-key-pair \
      --region "$region" \
      --key-name $key_pair_name \
      --query 'KeyMaterial' \
      --output text > temp/$key_pair_name.pem

    chmod 400 temp/$key_pair_name.pem
    ssh-keygen -y -f temp/$key_pair_name.pem > temp/$key_pair_name.pub

    # Set the correct permissions for the key pair
    chmod 400 temp/$key_pair_name.pem
  else
    echo "Key pair $key_pair_name already exists."
  fi
}

cleanup_instances() {
  instance_type=$1
  echo "Cleaning up ${instance_type} instances..."
  instance_ids=$(aws ec2 describe-instances --filters "Name=tag:EXP_TIME,Values=$LAST_EXP_TIME" "Name=tag:TYPE,Values=$instance_type" --query "Reservations[].Instances[].InstanceId" --output text | tr '\t' ' ')
  
  if [ -n "$instance_ids" ]; then
    aws ec2 terminate-instances --instance-ids $instance_ids || { echo "Failed to terminate $instance_type instances."; exit 1; }
    echo "$instance_type instances cleaned up successfully."
  else
    echo "No $instance_type instances found to clean up."
  fi
}


# Function to clean up previous experiment
cleanup_previous_experiment() {
  if [ -f temp/last_exp_time.txt ]; then
    . temp/last_exp_time.txt

    if [ -n "$LAST_EXP_TIME" ]; then
      echo "Last experiment time: $LAST_EXP_TIME"
      echo "The previous experiment will be cleaned up..."

      cleanup_instances "server"
      cleanup_instances "bot"
      cleanup_instances "prometheus"

      echo "Cleanup completed. LAST_EXP_TIME entry will be removed."
      rm temp/last_exp_time.txt  # Delete the last experiment time file after cleanup
    else
      echo "It appears to be the first time running the experiment as LAST_EXP_TIME is not set."
    fi
  else
    echo "First time running the experiment. No cleanup needed."
  fi
}

# Function to ask the user if they want to start a new experiment
start_new_experiment() {
  local exp_time=$1

  while true; do
    read -r -p "Do you want to start a new experiment? [y/N] " START_NEW_EXP
    case $START_NEW_EXP in
        [Yy]* )
          echo "Starting new experiment..."
          echo "LAST_EXP_TIME=$exp_time" > temp/last_exp_time.txt
          break;;
        [Nn]* )
          echo "Not starting new experiment. Exiting script."
          exit;;
        * ) echo "Please answer yes or no.";;
    esac
  done
}

# Function to manage the security group
manage_security_group() {
  SECURITY_GROUP_ID=$(aws ec2 describe-security-groups \
    --region "$AWS_REGION" \
    --filters "Name=group-name,Values=$SECURITY_GROUP_NAME" \
    --query 'SecurityGroups[0].GroupId' \
    --output text)

  if [ "$SECURITY_GROUP_ID" == "None" ]; then
    echo "Creating new security group: $SECURITY_GROUP_NAME..."
    SECURITY_GROUP_ID=$(aws ec2 create-security-group \
      --region "$AWS_REGION" \
      --group-name $SECURITY_GROUP_NAME \
      --description "Security group for Terraria server and bot" \
      --query 'GroupId' \
      --output text)

    # getting the default vpc cidr block 
    DEFAULT_VPC_CIDR=$(aws ec2 describe-vpcs \
      --filters Name=isDefault,Values=true \
      --query 'Vpcs[0].CidrBlock' \
      --region "$AWS_REGION" \
      --output text)

    # Add rules to the security group to allow necessary traffic
    aws ec2 authorize-security-group-ingress \
      --region "$AWS_REGION" \
      --group-id "$SECURITY_GROUP_ID" \
      --protocol tcp \
      --port 7777 \
      --cidr "$DEFAULT_VPC_CIDR"

    aws ec2 authorize-security-group-ingress \
      --region "$AWS_REGION" \
      --group-id "$SECURITY_GROUP_ID" \
      --protocol tcp \
      --port 9256 \
      --cidr "$DEFAULT_VPC_CIDR"

    aws ec2 authorize-security-group-ingress \
      --region "$AWS_REGION" \
      --group-id "$SECURITY_GROUP_ID" \
      --protocol tcp \
      --port 9090 \
      --cidr "$DEFAULT_VPC_CIDR"
  else
    echo "Security group $SECURITY_GROUP_NAME already exists."
  fi
}

# Function to create an instance
create_instance() {
  instance_name=$1
  instance_type=$2
  instance_id=$(aws ec2 run-instances \
    --region "$AWS_REGION" \
    --image-id "$AMI_ID" \
    --count 1 \
    --instance-type "$INSTANCE_TYPE" \
    --key-name $KEY_PAIR_NAME \
    --security-group-ids "$SECURITY_GROUP_ID" \
    --query 'Instances[0].InstanceId' \
    --output text)
  tag_instance "$instance_id" "$instance_name" "$instance_type"
  echo $instance_id
}

# Function to tag an instance
tag_instance() {
  instance_id=$1
  instance_name=$2
  instance_type=$3
  aws ec2 create-tags \
    --region "$AWS_REGION" \
    --resources "$instance_id" \
    --tags Key=Name,Value="$instance_name" Key=EXP_TIME,Value="$EXP_TIME" Key=TYPE,Value="$instance_type"
}

# Function to create bot instances
create_bot_instances() {
  declare -a bot_instance_ids
  for ((i=1; i<=$NUM_BOT_INSTANCES; i++))
  do
    bot_instance_id=$(create_instance "bot$i" "bot")
    bot_instance_ids+=($bot_instance_id)
  done
  echo "${bot_instance_ids[@]}"
}

# Function to get an instance state
get_instance_state() {
  instance_id=$1
  instance_name=$2
  echo "$instance_name state:"
  aws ec2 describe-instances --instance-ids "$instance_id" --query 'Reservations[].Instances[].State.Name'
}

# Function to wait for instances to be running
wait_for_instances() {
  instance_ids=("$@")
  for instance_id in "${instance_ids[@]}"
  do
    aws ec2 wait instance-running --instance-ids "$instance_id"
  done
}

# Function for AWS Availability
get_aws_availability_zone() {
  instance_id=$1
  echo $(aws ec2 describe-instances \
    --region "$AWS_REGION" \
    --instance-ids "$instance_id" \
    --query 'Reservations[0].Instances[0].Placement.AvailabilityZone' \
    --output text)
}

# for setting SSH Public Key
set_ssh_public_key() {
  instance_id=$1
  availability_zone=$2
  aws ec2-instance-connect send-ssh-public-key \
    --region "$AWS_REGION" \
    --instance-id "$instance_id" \
    --availability-zone "$availability_zone" \
    --instance-os-user ubuntu \
    --ssh-public-key file://temp/$KEY_PAIR_NAME.pub
}

# for getting public DNS
get_public_dns() {
  instance_id=$1
  echo $(aws ec2 describe-instances \
    --region "$AWS_REGION" \
    --instance-ids "$instance_id" \
    --query 'Reservations[0].Instances[0].PublicDnsName' \
    --output text)
}

# for SSH availability check
check_ssh_availability() {
  public_dns=$1
  until ssh -o StrictHostKeyChecking=no -o CheckHostIP=no -o ConnectTimeout=5 -i temp/$KEY_PAIR_NAME.pem ubuntu@"$public_dns" true; do
    echo "Waiting for SSH to be available..."
    sleep 5
  done
}

# for running remote commands
run_remote_commands() {
  public_dns=$1
  commands=$2
  ssh -i temp/$KEY_PAIR_NAME.pem ubuntu@"$public_dns" -o StrictHostKeyChecking=no -t "$commands"
}

# for bot instance setup
setup_bot_instance() {
  bot_instance_id=$1
  aws_availability_zone_bot=$(get_aws_availability_zone $bot_instance_id)
  set_ssh_public_key $bot_instance_id $aws_availability_zone_bot
  bot_public_dns=$(get_public_dns $bot_instance_id)
  check_ssh_availability $bot_public_dns
  run_remote_commands $bot_public_dns "$remote_install_commands_bot"
  BOT_PUBLIC_DNS_ADDRESSES+=("$bot_public_dns")
}

remote_install_commands_server=$(cat <<CMD
  sudo apt update -y
  sudo apt install zip unzip -y
  cd ~
  wget https://dot.net/v1/dotnet-install.sh -O dotnet-install.sh
  chmod +x dotnet-install.sh
  ./dotnet-install.sh --version latest
  echo "export DOTNET_ROOT=\$HOME/.dotnet" >> ~/.bashrc
  echo "export PATH=\$PATH:\$HOME/.dotnet:\$HOME/.dotnet/tools" >> ~/.bashrc
  source ~/.bashrc
  dir_name="$DIR_NAME"
  mkdir -p "\$dir_name"
  cd "\$dir_name"
  mkdir -p server bot
  cd server
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
  mv yardstick-$TERRASTICK_VERSION/terrastick/Deployment/metrics-configs/server-process-exporter.yaml ../server/process-exporter-0.7.10.linux-amd64/
CMD
)

# start the server instance
remote_start_commands_server=$(cat <<CMD
  source ~/.bashrc
  cd ~/$DIR_NAME/server
  screen -L -S server -d -m bash -c "./TShock.Server -world ~/$DIR_NAME/server/worlds/$WORLD_NAME.wld" || echo "Could not start server in screen"
  sleep 10
  cd ~/$DIR_NAME/server/process-exporter-0.7.10.linux-amd64
  screen -L -S process-exporter -d -m bash -c "./process-exporter -config.path server-process-exporter.yaml -web.listen-address \$TERRASTICK_IP:9256" || echo "Could not start process exporter in screen"
CMD
)

remote_install_commands_bot=$(cat <<CMD
  sudo apt update -y
  sudo apt install zip unzip -y
  TERRASTICK_WORKLOAD=$TERRASTICK_WORKLOAD
  TERRASTICK_IP=$TERRARIA_SERVER_PRIVATE_IP
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
  wget https://dot.net/v1/dotnet-install.sh -O dotnet-install.sh
  chmod +x dotnet-install.sh
  ./dotnet-install.sh --version latest
  source ~/.bashrc
  dir_name="$DIR_NAME"
  mkdir -p "\$dir_name"
  cd "\$dir_name"
  mkdir -p bot
  cd bot
  curl -sL https://github.com/atlarge-research/yardstick/archive/refs/tags/$TERRASTICK_VERSION.zip -o terrastick.zip
  unzip terrastick.zip && rm terrastick.zip
  cd yardstick-$TERRASTICK_VERSION/terrastick/PlayerEmulations/TrClientTest && dotnet build -r linux-x64 -c Release --no-self-contained || echo "Build failed"
CMD
)

# start the bot instance

remote_start_commands_bot=$(cat <<CMD
  source ~/.bashrc
  cd ~/$DIR_NAME/bot/yardstick-$TERRASTICK_VERSION/terrastick/PlayerEmulations/TrClientTest/bin/Release/net6.0/linux-x64/
  screen -L -S bot -d -m bash -c "./TrClientTest" || echo "Could not start bot in screen"
CMD
)

remote_install_commands_prometheus=$(cat <<CMD
  sudo apt update -y
  sudo apt install zip unzip -y
  cd ~
  wget https://dot.net/v1/dotnet-install.sh -O dotnet-install.sh
  chmod +x dotnet-install.sh
  ./dotnet-install.sh --version latest
  echo "export DOTNET_ROOT=\$HOME/.dotnet" >> ~/.bashrc
  echo "export PATH=\$PATH:\$HOME/.dotnet:\$HOME/.dotnet/tools" >> ~/.bashrc
  echo "export TERRASTICK_IP=$TERRARIA_SERVER_PRIVATE_IP" >> ~/.bashrc
  source ~/.bashrc
  dir_name="$DIR_NAME"
  mkdir -p "\$dir_name"
  cd "\$dir_name"
  mkdir -p prometheus bot
  cd prometheus
  curl -sL  https://github.com/prometheus/prometheus/releases/download/v2.37.8/prometheus-2.37.8.linux-amd64.tar.gz -o prometheus.gz
  tar -xvf prometheus.gz && rm prometheus.gz
  cd ../bot
  curl -sL https://github.com/atlarge-research/yardstick/archive/refs/tags/$TERRASTICK_VERSION.zip -o terrastick.zip
  unzip terrastick.zip && rm terrastick.zip
  mv yardstick-$TERRASTICK_VERSION/terrastick/Deployment/metrics-configs/prometheus-terrastick.yml ../prometheus/prometheus-2.37.8.linux-amd64/
CMD
)

remote_start_commands_prometheus=$(cat <<CMD
  source ~/.bashrc
  cd ~/$DIR_NAME/prometheus/prometheus-2.37.8.linux-amd64
  screen -L -S prometheus -d -m bash -c "./prometheus --config.file=prometheus-terrastick.yml" || echo "Could not start prometheus in screen"
CMD
)

# main script
create_key_pair $KEY_PAIR_NAME $AWS_REGION
cleanup_previous_experiment
start_new_experiment $EXP_TIME
manage_security_group
TERRARIA_SERVER_INSTANCE_ID=$(create_instance "terraria-server" "server") && echo "Created server instance with id $TERRARIA_SERVER_INSTANCE_ID"
BOT_INSTANCE_IDS=$(create_bot_instances) && echo "Created bot instances with ids $BOT_INSTANCE_IDS"
IFS=" " read -ra BOT_IDS <<< "$BOT_INSTANCE_IDS"
PROMETHEUS_SERVER_INSTANCE_ID=$(create_instance "prometheus" "prometheus") && echo "Created prometheus instance with id $PROMETHEUS_SERVER_INSTANCE_ID"
get_instance_state "$TERRARIA_SERVER_INSTANCE_ID" "Server instance"
for BOT_INSTANCE_ID in "${BOT_IDS[@]}"
do
  get_instance_state "$BOT_INSTANCE_ID" "Bot instance"
done
get_instance_state "$PROMETHEUS_SERVER_INSTANCE_ID" "Prometheus instance"
wait_for_instances "$TERRARIA_SERVER_INSTANCE_ID" "${BOT_IDS[@]}" "$PROMETHEUS_SERVER_INSTANCE_ID"

# find out the private ip address of the terraia server instance
TERRARIA_SERVER_PRIVATE_IP=$(aws ec2 describe-instances \
  --instance-ids "$TERRARIA_SERVER_INSTANCE_ID" \
  --query 'Reservations[].Instances[].PrivateIpAddress' \
  --output text)

# Server setup
AWS_AVAILABILITY_ZONE_SERVER=$(get_aws_availability_zone $TERRARIA_SERVER_INSTANCE_ID)
set_ssh_public_key $TERRARIA_SERVER_INSTANCE_ID $AWS_AVAILABILITY_ZONE_SERVER
TERRARIA_SERVER_PUBLIC_DNS=$(get_public_dns $TERRARIA_SERVER_INSTANCE_ID)
check_ssh_availability $TERRARIA_SERVER_PUBLIC_DNS
run_remote_commands $TERRARIA_SERVER_PUBLIC_DNS "$remote_install_commands_server"
run_remote_commands $TERRARIA_SERVER_PUBLIC_DNS "$remote_start_commands_server"

# Prometheus setup
AWS_AVAILABILITY_ZONE_PROMETHEUS=$(get_aws_availability_zone $PROMETHEUS_SERVER_INSTANCE_ID)
set_ssh_public_key $PROMETHEUS_SERVER_INSTANCE_ID $AWS_AVAILABILITY_ZONE_PROMETHEUS
PROMETHEUS_SERVER_PUBLIC_DNS=$(get_public_dns $PROMETHEUS_SERVER_INSTANCE_ID)
check_ssh_availability $PROMETHEUS_SERVER_PUBLIC_DNS
run_remote_commands $PROMETHEUS_SERVER_PUBLIC_DNS "$remote_install_commands_prometheus"
run_remote_commands $PROMETHEUS_SERVER_PUBLIC_DNS "$remote_start_commands_prometheus"

# Bot setup
for bot_instance_id in "${BOT_IDS[@]}"; do
  setup_bot_instance $bot_instance_id
done
