#!/usr/bin/env bash

# Agree with EULA
echo "eula=true" > eula.txt

# Download server
wget https://s3.amazonaws.com/Minecraft.Download/versions/1.11/minecraft_server.1.11.jar

# Start server. Ignore the version.
java -Xmx1024M -Xms1024M -jar minecraft_server*.jar nogui

