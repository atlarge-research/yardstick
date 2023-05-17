#!/bin/bash

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

# Check if the key pair exists and create it if not
KEY_PAIR_EXISTS=$(aws ec2 describe-key-pairs \
  --region "$AWS_REGION" \
  --filters "Name=key-name,Values=$KEY_PAIR_NAME" \
  --query 'KeyPairs[0].KeyName' \
  --output text)

if [ "$KEY_PAIR_EXISTS" == "None" ]; then
  echo "Creating a temp folder..."
  mkdir -p temp
  echo "Creating new key pair: $KEY_PAIR_NAME..."
  aws ec2 create-key-pair \
    --region "$AWS_REGION" \
    --key-name $KEY_PAIR_NAME \
    --query 'KeyMaterial' \
    --output text > temp/$KEY_PAIR_NAME.pem

  chmod 400 temp/$KEY_PAIR_NAME.pem
  ssh-keygen -y -f temp/$KEY_PAIR_NAME.pem > temp/$KEY_PAIR_NAME.pub

  # Set the correct permissions for the key pair
  chmod 400 temp/$KEY_PAIR_NAME.pem
else
  echo "Key pair $KEY_PAIR_NAME already exists."
fi

# Check if the security group exists and create it if not
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
    --port 22 \
    --cidr "0.0.0.0/0" # Adjust the CIDR block to restrict access as needed

  aws ec2 authorize-security-group-ingress \
    --region "$AWS_REGION" \
    --group-id "$SECURITY_GROUP_ID" \
    --protocol tcp \
    --port 7777 \
    --cidr "$DEFAULT_VPC_CIDR"
else
  echo "Security group $SECURITY_GROUP_NAME already exists."
fi

# Create the Terraria server instance
echo "Creating Terraria server instance..."
TERRARIA_SERVER_INSTANCE_ID=$(aws ec2 run-instances \
  --region "$AWS_REGION" \
  --image-id "$AMI_ID" \
  --count 1 \
  --instance-type "$INSTANCE_TYPE" \
  --key-name $KEY_PAIR_NAME \
  --security-group-ids "$SECURITY_GROUP_ID" \
  --query 'Instances[0].InstanceId' \
  --output text)

echo "Terraria server instance created with ID: $TERRARIA_SERVER_INSTANCE_ID"

# Create bot instances
declare -a BOT_INSTANCE_IDS
for ((i=1; i<=$NUM_BOT_INSTANCES; i++))
do
  BOT_INSTANCE_ID=$(aws ec2 run-instances \
  --region "$AWS_REGION" \
  --image-id "$AMI_ID" \
  --count 1 \
  --instance-type "$INSTANCE_TYPE" \
  --key-name $KEY_PAIR_NAME \
  --security-group-ids "$SECURITY_GROUP_ID" \
  --query 'Instances[0].InstanceId' \
  --output text)
  BOT_INSTANCE_IDS+=($BOT_INSTANCE_ID)
done

echo "Terraria bot instances created with IDs: ${BOT_INSTANCE_IDS[@]}"

# Print the instance states
echo "Server instance state:"
aws ec2 describe-instances --instance-ids "$TERRARIA_SERVER_INSTANCE_ID" --query 'Reservations[].Instances[].State.Name'
for BOT_INSTANCE_ID in "${BOT_INSTANCE_IDS[@]}"
do
  echo "Bot instance $BOT_INSTANCE_ID state:"
  aws ec2 describe-instances --instance-ids "$BOT_INSTANCE_ID" --query 'Reservations[].Instances[].State.Name'
done

# Wait for instances to be running
aws ec2 wait instance-running --instance-ids "$TERRARIA_SERVER_INSTANCE_ID"
for BOT_INSTANCE_ID in "${BOT_INSTANCE_IDS[@]}"
do
  aws ec2 wait instance-running --instance-ids "$BOT_INSTANCE_ID"
done

remote_install_commands_server=$(cat <<CMD
  sudo apt-get update -y
  cd ~
  wget https://dot.net/v1/dotnet-install.sh -O dotnet-install.sh
  chmod +x dotnet-install.sh
  ./dotnet-install.sh --version latest
  echo "export DOTNET_ROOT=\$HOME/.dotnet" >> ~/.bashrc
  echo "export PATH=\$PATH:\$HOME/.dotnet:\$HOME/.dotnet/tools" >> ~/.bashrc
  source ~/.bashrc
CMD
)

remote_install_commands_bot=$(cat <<CMD
  sudo apt-get update -y
  cd ~
  wget https://dot.net/v1/dotnet-install.sh -O dotnet-install.sh
  chmod +x dotnet-install.sh
  ./dotnet-install.sh --version latest
  echo "export DOTNET_ROOT=\$HOME/.dotnet" >> ~/.bashrc
  echo "export PATH=\$PATH:\$HOME/.dotnet:\$HOME/.dotnet/tools" >> ~/.bashrc
  source ~/.bashrc
CMD
)

AWS_AVAILABILITY_ZONE_SERVER=$(aws ec2 describe-instances \
  --region "$AWS_REGION" \
  --instance-ids "$TERRARIA_SERVER_INSTANCE_ID" \
  --query 'Reservations[0].Instances[0].Placement.AvailabilityZone' \
  --output text)

# Install dotnet on the server and bot instances
aws ec2-instance-connect send-ssh-public-key \
  --region "$AWS_REGION" \
  --instance-id "$TERRARIA_SERVER_INSTANCE_ID" \
  --availability-zone "$AWS_AVAILABILITY_ZONE_SERVER" \
  --instance-os-user ubuntu \
  --ssh-public-key file://temp/$KEY_PAIR_NAME.pub

TERRARIA_SERVER_PUBLIC_DNS=$(aws ec2 describe-instances \
  --region "$AWS_REGION" \
  --instance-ids "$TERRARIA_SERVER_INSTANCE_ID" \
  --query 'Reservations[0].Instances[0].PublicDnsName' \
  --output text)

until ssh -o StrictHostKeyChecking=no -o CheckHostIP=no -o ConnectTimeout=5 -i temp/$KEY_PAIR_NAME.pem ubuntu@"$TERRARIA_SERVER_PUBLIC_DNS" true; do
  echo "Waiting for SSH to be available..."
  sleep 5
done

# Now you can run your remote commands:
ssh -i temp/$KEY_PAIR_NAME.pem ubuntu@"$TERRARIA_SERVER_PUBLIC_DNS" -o StrictHostKeyChecking=no -t "$remote_install_commands_server"



for BOT_INSTANCE_ID in "${BOT_INSTANCE_IDS[@]}"
do
  AWS_AVAILABILITY_ZONE_BOT=$(aws ec2 describe-instances \
  --region "$AWS_REGION" \
  --instance-ids "$BOT_INSTANCE_ID" \
  --query 'Reservations[0].Instances[0].Placement.AvailabilityZone' \
  --output text)

  aws ec2-instance-connect send-ssh-public-key \
    --region "$AWS_REGION" \
    --instance-id "$BOT_INSTANCE_ID" \
    --availability-zone "$AWS_AVAILABILITY_ZONE_BOT" \
    --instance-os-user ubuntu \
    --ssh-public-key file://temp/$KEY_PAIR_NAME.pub

  BOT_PUBLIC_DNS=$(aws ec2 describe-instances \
  --region "$AWS_REGION" \
  --instance-ids "$BOT_INSTANCE_ID" \
  --query 'Reservations[0].Instances[0].PublicDnsName' \
  --output text)

  until ssh -o StrictHostKeyChecking=no -o CheckHostIP=no -o ConnectTimeout=5 -i temp/$KEY_PAIR_NAME.pem ubuntu@"$BOT_PUBLIC_DNS" true; do
  echo "Waiting for SSH to be available..."
  sleep 5
  done

  # Now you can run your remote commands:
  ssh -i temp/$KEY_PAIR_NAME.pem ubuntu@"$BOT_PUBLIC_DNS" -o StrictHostKeyChecking=no -t "$remote_install_commands_bot"
done

# Cleanup
aws ec2 terminate-instances --instance-ids "$TERRARIA_SERVER_INSTANCE_ID"
for BOT_INSTANCE_ID in "${BOT_INSTANCE_IDS[@]}"
do
  aws ec2 terminate-instances --instance-ids "$BOT_INSTANCE_ID"
done

aws ec2 delete-key-pair --key-name "$KEY_PAIR_NAME"

rm -rf temp
