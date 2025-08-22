#!/bin/bash

#Project directory
PROJECT_DIR="."

# Enter venv inside the project directory
source "$PROJECT_DIR/venv/bin/activate"

# Change directory to the project directory
cd "$PROJECT_DIR"

# Run the Python script
python3 "main.py"