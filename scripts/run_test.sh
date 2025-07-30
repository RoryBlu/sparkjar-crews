#!/bin/bash
# Run book ingestion test with proper Python path

# Set Python path to include current directory
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Load environment variables from parent .env
if [ -f "../../.env" ]; then
    export $(cat ../../.env | grep -v '^#' | xargs)
fi

# Run the test
python3 test_book_ingestion_5files.py