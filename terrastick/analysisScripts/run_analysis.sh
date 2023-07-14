#!/bin/bash

# Create a virtual environment and install the required packages
python -m venv .env
source .env/bin/activate
pip install -r requirements.txt
python analysis.py