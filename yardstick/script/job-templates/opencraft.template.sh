#!/bin/bash
#SBATCH --job-name opencraft-yardstick
#SBATCH --time=<<<TIMEOUT>>>
#SBATCH -N <<<NODES>>>

. /etc/bashrc
. /etc/profile.d/modules.sh
module add java/jdk-1.8.0
module add python/3.6.0

export SERVER_HOSTNAME=`srun -r 0 -N 1 -n 1 bash -c 'hostname'`

# Start the server
echo "Starting the server!"
srun -r 0 -N 1 -n 1 bash -c 'bash -c "<<<RUN_SERVER_COMMAND>>> > server.log"' &
echo "Sleep until server finished starting!"
sleep '<<<CLIENT_START_DELAY>>>'

# Start the clients
for ((i=1;i<='<<<CLIENT_AMOUNT>>>';i++)); do
  echo "Starting client $i!"
  srun -r $i -N 1 -n 1 bash -c '<<<RUN_CLIENT_COMMAND>>> > client'$i'.log' &
  sleep '<<<PLAYER_JOIN_INTERVAL>>>'
done

echo "Finished starting clients. Sleeping until run complete."
sleep '<<<CLIENT_RUN_TIME>>>'

# Shutdown the server
echo "Shutting down the server!"
srun -r 0 -N 1 -n 1 bash -c 'killall java'

# Wait until the server and clients have finished running
echo "Waiting until shutdown complete..."
wait
echo "Shutdown completed"
