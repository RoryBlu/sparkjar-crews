#!/usr/bin/env python3
"""
Final test script to run Memory Maker Crew with Vervelyn corporate policy data.
This version properly loads environment variables and uses the crew directly.
"""

import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directories to path for imports
crew_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(crew_dir))

# Load environment variables from the crew directory
env_path = crew_dir / '.env'
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Loaded environment variables from {env_path}")
else:
    # Try parent directory
    parent_env = crew_dir.parent.parent / '.env'
    if parent_env.exists():
        load_dotenv(parent_env)
        print(f"✅ Loaded environment variables from {parent_env}")

from crew import MemoryMakerCrew

def test_vervelyn_policy():
    """Test the Memory Maker Crew with Vervelyn corporate policy."""
    
    # Verify API keys
    if not os.getenv("OPENAI_API_KEY"):
        print("\n❌ Error: OPENAI_API_KEY not found in environment")
        return
    else:
        print("✅ OPENAI_API_KEY is set")
    
    if not os.getenv("API_SECRET_KEY"):
        print("⚠️  API_SECRET_KEY not found, using test key")
        os.environ["API_SECRET_KEY"] = "test-secret-key-for-local-testing"
    else:
        print("✅ API_SECRET_KEY is set")
    
    # Load the test payload
    payload_path = "/Users/r.t.rawlings/sparkjar-crew/_reorg/sparkjar-crew-api/test_payloads/vervelyn_corporate_policy_payload.json"
    
    with open(payload_path, 'r') as f:
        payload = json.load(f)
    
    print("\n=== Memory Maker Crew Test - Vervelyn Corporate Policy ===\n")
    
    # Extract the request data
    request_data = payload['data']
    
    print(f"Actor Type: {request_data['actor_type']}")
    print(f"Actor ID: {request_data['actor_id']}")
    print(f"Client User ID: {request_data['client_user_id']}")
    print(f"Text Length: {len(request_data['text_content'])} characters")
    
    # Display first 200 chars of the text
    print(f"\nText Preview: {request_data['text_content'][:200]}...")
    
    # Initialize the crew with actor context
    print("\n🚀 Initializing Memory Maker Crew...")
    try:
        crew = MemoryMakerCrew(
            client_user_id=request_data['client_user_id'],
            actor_type=request_data['actor_type'],
            actor_id=request_data['actor_id']
        )
        print("✅ Crew initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize crew: {e}")
        return
    
    # Prepare inputs for the crew
    inputs = {
        'text_content': request_data['text_content'],
        'actor_type': request_data['actor_type'],
        'actor_id': request_data['actor_id'],
        'client_user_id': request_data['client_user_id']
    }
    
    # Execute the crew
    print("\n🔄 Processing text and extracting memories...")
    print("This may take a few minutes...\n")
    
    try:
        # Run the crew
        result = crew.kickoff(inputs=inputs)
        
        print("\n✅ Crew execution completed!")
        
        # Display results
        print("\n=== Crew Output ===")
        if hasattr(result, 'output'):
            print(result.output)
        else:
            print(result)
        
        # Display raw result
        print("\n=== Raw Result ===")
        print(f"Type: {type(result)}")
        print(f"String representation: {str(result)[:500]}...")
        
        # If result has attributes, display them
        if hasattr(result, '__dict__'):
            print("\n=== Result Attributes ===")
            for key, value in result.__dict__.items():
                if not key.startswith('_'):
                    if isinstance(value, str) and len(value) > 200:
                        print(f"{key}: {value[:200]}...")
                    else:
                        print(f"{key}: {value}")
                    
    except Exception as e:
        print(f"\n❌ Crew execution failed: {e}")
        import traceback
        traceback.print_exc()
        
        # Try to provide more context
        print("\n=== Debug Information ===")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Python path: {sys.path[:3]}...")
        print(f"Crew directory: {crew_dir}")

if __name__ == "__main__":
    test_vervelyn_policy()