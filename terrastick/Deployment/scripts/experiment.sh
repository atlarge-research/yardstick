#!/bin/bash

# to-dos here
# 1) unified setup for aws, azure
# 2) ask which env do you want to run the experiment in
# 3) check if you have the required config file and if all the required variables are defined

# Virtual environment setup
python -m venv .env
source .env/bin/activate
pip install -r requirements.txt

# Prompt the user to choose an environment
echo "Which environment should the experiment run in?"
echo "1) AWS"
echo "2) Azure (not supported yet)"
echo "3) DAS5"
echo "4) DAS6"
read choice

# Checking if the config file exists
case $choice in
  1)
    if [ ! -f ./configs/aws-config.txt ]; then
      echo "ERROR: aws-config.txt not found" && exit 1
    fi
    ;;
  # 2)
  #   if [ ! -f ./configs/azure-config.txt ]; then
  #     echo "ERROR: azure-config.txt not found" && exit 1
  #   fi
  #   ;;
  3)
    if [ ! -f ./configs/das-config.txt ]; then
      echo "ERROR: das-config.txt not found" && exit 1
    fi
    . ./configs/das-config.txt
    if [ "$DAS_VERSION_TO_USE" -ne 5 ]; then
        echo "ERROR: DAS_VERSION_TO_USE should be 5" && exit 1
    fi
    ;;
  4)
    if [ ! -f ./configs/das-config.txt ]; then
      echo "ERROR: das-config.txt not found" && exit 1
    fi
        . ./configs/das-config.txt
    if [ "$DAS_VERSION_TO_USE" -ne 6 ]; then
        echo "ERROR: DAS_VERSION_TO_USE should be 6" && exit 1
    fi
    ;;
esac

# Execute the respective script
case $choice in
  1)
    ./aws.sh
    ;;
  # 2)
  #   ./azure.sh
  #   ;;
  3)
    ./das.sh
    ;;
  4)
    ./das.sh
    ;;
esac