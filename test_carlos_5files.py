#!/usr/bin/env python3
"""Direct test of book ingestion production crew"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Ensure we're in the right directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Import production kickoff directly
from crews.book_ingestion_crew import crew_production

def main():
    """Test Carlos Gonzalez manuscript - 5 files only"""
    
    inputs = {
        "google_drive_folder_path": "SparkJar Productions/Clients/Vervelyn Publishing House/Books/El Barón de la Droga, Una Novela/Book Manuscript from Author",
        "language": "Spanish",  
        "client_user_id": "86ba2fcc-fe9e-430a-a88f-9da8dc0dc4e0",
        "book_title": "El Barón de la Droga",
        "book_author": "Carlos Gonzalez",
        "process_pages_limit": 5
    }
    
    print(f"\n{'='*60}")
    print("Carlos Gonzalez Book Ingestion - 5 Files Test")
    print(f"{'='*60}")
    print(f"Start: {datetime.now()}")
    print(f"Files: First 5 only")
    print(f"{'='*60}\n")
    
    try:
        result = crew_production.kickoff(inputs)
        print(f"\n{'='*60}")
        print("SUCCESS!")
        print(f"Result: {result}")
        print(f"End: {datetime.now()}")
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()