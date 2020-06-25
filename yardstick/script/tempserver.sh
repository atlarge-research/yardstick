!/usr/bin/env bash

JOB_TEMP_DIR="/local/$(whoami)/temp_job_data"
CONFIG=$1


mkdir -p "$JOB_TEMP_DIR"
cp -r template/* $JOB_TEMP_DIR
cp $CONFIG $JOB_TEMP_DIR/config/opencraft.yml

cd $JOB_TEMP_DIR

# Start server. Ignore the version.
java -Xmx8192M -Xms512M -jar $JOB_TEMP_DIR/opencraft.jar
rm -rf "$JOB_TEMP_DIR"

