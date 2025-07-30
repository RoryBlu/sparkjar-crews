#!/usr/bin/env python3
"""Test book ingestion with 5 files only"""

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

def test_book_ingestion():
    """Test ingesting 5 pages of Carlos Gonzalez manuscript"""
    
    # Test inputs
    inputs = {
        "job_key": "book_ingestion_crew",  # Required for schema validation
        "google_drive_folder_path": "https://drive.google.com/drive/u/0/folders/1HFDpMUHT0wjVWdWB9XIUMYavmq23I4JO",
        "language": "Spanish",
        "client_user_id": "3a411a30-1653-4caf-acee-de257ff50e36",
        "actor_type": "synth",
        "actor_id": "e30fc9f3-57da-4cf0-84e7-ea9188dd5fba",
        "book_title": "La Baron de la Drogo",
        "book_author": "Castor Gonzalez",
        "book_description": "The autobiography of Castor Gonzalez",
        "process_pages_limit": 5  # Only process 5 files for testing (change to 0 for full run)
    }
    
    print(f"\n{'='*60}")
    print("Book Ingestion Test - 5 Files Only")
    print(f"{'='*60}")
    print(f"Start time: {datetime.now()}")
    print(f"Language: {inputs['language']}")
    print(f"Folder: {inputs['google_drive_folder_path']}")
    print(f"Limit: {inputs['process_pages_limit']} files")
    print(f"{'='*60}\n")
    
    try:
        # Run the crew
        result = kickoff(inputs)
        
        print(f"\n{'='*60}")
        print("Test Complete!")
        print(f"{'='*60}")
        print(f"End time: {datetime.now()}")
        
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
    # Check for required env vars
    required_env = ["OPENAI_API_KEY", "DATABASE_URL_DIRECT"]
    missing = [var for var in required_env if not os.getenv(var)]
    
    if missing:
        print(f"❌ Missing required environment variables: {missing}")
        print("Please set these in your .env file")
        sys.exit(1)
    
    # Run test
    success = test_book_ingestion()
    sys.exit(0 if success else 1)