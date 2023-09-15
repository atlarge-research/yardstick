#!/bin/bash

# Create a virtual environment and install the required packages
module load python/3.6.0
python3.6 -m venv .env
source .env/bin/activate
pip install -r requirements.txt
echo "getting durations from start times"
python3.6 get_times.py
echo "getting prometheus data"
python3.6 get_prometheus_data.py
echo "performing analysis"
python3.6 analysis.py
