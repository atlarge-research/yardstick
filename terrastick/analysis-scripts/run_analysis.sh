#!/bin/bash

# Create a virtual environment and install the required packages
module load python/3.6.0
python3.6 -m venv .env
source .env/bin/activate
pip install -r requirements.txt
python3.6 get_exp_times.py
python3.6 get_prometheus_logs.py
python3.6 analysis.py