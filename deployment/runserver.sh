#!/usr/bin/env bash

# Agree with EULA
echo "eula=true" > eula.txt

# Download server

# Start server. Ignore the version.
java -Xmx1024M -Xms1024M -jar minecraft_server.1.15.jar nogui

