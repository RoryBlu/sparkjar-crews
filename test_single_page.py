#!/usr/bin/env python3
"""Test book ingestion with just 1 file to debug faster"""

import os
import sys
import json
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging to see progress
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# Add sparkjar-shared to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'sparkjar-shared'))

# Import the ONE crew
from crews.book_ingestion_crew.crew import kickoff

def test_single_page():
    """Test ingesting just 1 page to debug"""
    
    # Test inputs
    inputs = {
        "job_key": "book_ingestion_crew",
        "google_drive_folder_path": "https://drive.google.com/drive/u/0/folders/1HFDpMUHT0wjVWdWB9XIUMYavmq23I4JO",
        "language": "Spanish",
        "client_user_id": "3a411a30-1653-4caf-acee-de257ff50e36",
        "actor_type": "synth",
        "actor_id": "e30fc9f3-57da-4cf0-84e7-ea9188dd5fba",
        "book_title": "La Baron de la Drogo",
        "book_author": "Castor Gonzalez",
        "book_description": "The autobiography of Castor Gonzalez",
        "process_pages_limit": 1  # Only process 1 file for quick testing
    }
    
    print(f"\n{'='*60}")
    print("Book Ingestion Test - 1 File Only")
    print(f"{'='*60}")
    
    try:
        # Run the crew
        result = kickoff(inputs)
        
        print(f"\n{'='*60}")
        print("Test Complete!")
        print(f"{'='*60}")
        
        # Pretty print result
        print("\nResult:")
        print(json.dumps(result, indent=2, default=str))
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    # Run test
    success = test_single_page()
    sys.exit(0 if success else 1)