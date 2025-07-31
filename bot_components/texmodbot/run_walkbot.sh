#!/bin/bash
# Script to run the walkbot

# Default values
SERVER="127.0.0.1:30000"
USERNAME="walkbot"
PASSWORD="walkbot123"
MODE="random"         # Options: random, circular, static, follow
SPEED="100"
TIMEOUT="120"

# Target coordinates for follow mode
TARGET_X="0"
TARGET_Y="8.5"  # Default Y coordinate at standard player height
TARGET_Z="0"

# Process command-line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --mode|-m)
      MODE="$2"
      shift 2
      ;;
    --target-x)
      TARGET_X="$2"
      shift 2
      ;;
    --target-y)
      TARGET_Y="$2"
      shift 2
      ;;
    --target-z)
      TARGET_Z="$2"
      shift 2
      ;;
    --speed|-s)
      SPEED="$2"
      shift 2
      ;;
    --timeout|-t)
      TIMEOUT="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      shift
      ;;
  esac
done

echo "Starting walkbot connecting to $SERVER"
echo "Movement mode: $MODE, Speed: $SPEED seconds between updates"

# Prepare command based on mode
CMD="cargo run --bin walkbot -- $SERVER \
  --username $USERNAME \
  --password $PASSWORD \
  --mode $MODE \
  --speed $SPEED \
  --quit-after-seconds $TIMEOUT"

# Add target coordinates for follow mode
if [ "$MODE" = "follow" ]; then
  echo "Target coordinates: X=$TARGET_X, Y=$TARGET_Y, Z=$TARGET_Z"
  # Use equals sign format to avoid issues with negative values
  CMD="$CMD --target-x=$TARGET_X --target-y=$TARGET_Y --target-z=$TARGET_Z"
  
  # Debug information
  echo "Running command: $CMD"
fi

# Run the walkbot with the specified parameters
$CMD
