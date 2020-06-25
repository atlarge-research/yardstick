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
srun -r 0 -N 1 -n 1 bash -c 'screen -S "opencraft-server" -md bash -c "<<<RUN_SERVER_COMMAND>>> > server.log"' &
sleep '<<<CLIENT_START_DELAY>>>'

# Start the clients
for ((i=0;i<='<<<CLIENT_AMOUNT>>>';i++)); do
  srun -r 1 -N '<<<CLIENT_AMOUNT>>>' -n '<<<CLIENT_AMOUNT>>>' bash -c '<<<RUN_CLIENT_COMMAND>>> > client'$i'.log' &
  sleep '<<<PLAYER_JOIN_INTERVAL>>>'
done

sleep '<<<CLIENT_RUN_TIME>>>'

# Shutdown the server
srun -r 0 -N 1 -n 1 bash -c 'screen -r "opencraft-server" -X stuff "<<<STOP_SERVER_COMMAND>>>"'

# Wait until the server and clients have finished running
wait
