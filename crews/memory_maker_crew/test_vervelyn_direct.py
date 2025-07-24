#!/usr/bin/env python3
"""
Direct test script to run Memory Maker Crew with Vervelyn corporate policy data.
This version uses the crew directly without the handler to avoid import issues.
"""

import json
import os
import sys
from pathlib import Path

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from crews.memory_maker_crew.crew import MemoryMakerCrew

def test_vervelyn_policy():
    """Test the Memory Maker Crew with Vervelyn corporate policy."""
    
    # Load the test payload
    payload_path = "/Users/r.t.rawlings/sparkjar-crew/_reorg/sparkjar-crew-api/test_payloads/vervelyn_corporate_policy_payload.json"
    
    with open(payload_path, 'r') as f:
        payload = json.load(f)
    
    print("=== Memory Maker Crew Test - Vervelyn Corporate Policy ===\n")
    
    # Extract the request data
    request_data = payload['data']
    
    print(f"Actor Type: {request_data['actor_type']}")
    print(f"Actor ID: {request_data['actor_id']}")
    print(f"Client User ID: {request_data['client_user_id']}")
    print(f"Text Length: {len(request_data['text_content'])} characters")
    print(f"Metadata: {json.dumps(request_data.get('metadata', {}), indent=2)}")
    
    # Set up environment
    if not os.getenv("OPENAI_API_KEY"):
        print("\n❌ Error: OPENAI_API_KEY not set in environment")
        print("Please set it with: export OPENAI_API_KEY='your-key-here'")
        return
    
    # Set up test API secret key if needed
    if not os.getenv("API_SECRET_KEY"):
        print("\n⚠️  Warning: API_SECRET_KEY not set, using test key")
        os.environ["API_SECRET_KEY"] = "test-secret-key-for-local-testing"
    
    # Initialize the crew with actor context
    print("\n🚀 Initializing Memory Maker Crew...")
    crew = MemoryMakerCrew(
        client_user_id=request_data['client_user_id'],
        actor_type=request_data['actor_type'],
        actor_id=request_data['actor_id']
    )
    
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
        result = crew.kickoff(inputs=inputs)
        
        print("\n✅ Crew execution completed!")
        
        # Display results
        print("\n=== Crew Output ===")
        if hasattr(result, 'output'):
            print(result.output)
        else:
            print(result)
        
        # If result has attributes, display them
        if hasattr(result, '__dict__'):
            print("\n=== Result Details ===")
            for key, value in result.__dict__.items():
                if not key.startswith('_'):
                    print(f"{key}: {value}")
                    
    except Exception as e:
        print(f"\n❌ Crew execution failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_vervelyn_policy()