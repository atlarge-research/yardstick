#!/bin/bash

output_file="diskstatresult.csv"
echo "Timestamp,Major,Minor,Device,ReadsCompleted,ReadsMerged,ReadSectors,ReadTime,WritesCompleted,WritesMerged,WriteSectors,WriteTime,IOInProgress,IOTime,WeightedIOTime"

while true; do
  timestamp=$(($(date +%s%N) / 1000000))
  awk -v ts="$timestamp" '{print ts","$1","$2","$3","$4","$5","$6","$7","$8","$9","$10","$11","$12","$13","$14}' /proc/diskstats
  sleep 0.1
done
