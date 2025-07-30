#!/bin/bash

# Setup script for test environment
echo "Setting up test environment for SparkJAR Crews..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install main requirements
echo "Installing main requirements..."
pip install -r requirements.txt

# Install test requirements
echo "Installing test requirements..."
pip install -r requirements-test.txt

# Install sparkjar-shared in development mode
echo "Installing sparkjar-shared..."
cd ../sparkjar-shared
pip install -e .
cd ../sparkjar-crews

echo "Test environment setup complete!"
echo "To activate the environment, run: source venv/bin/activate"