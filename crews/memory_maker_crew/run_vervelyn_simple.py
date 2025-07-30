#!/usr/bin/env python3
"""
Simplest possible way to run the memory maker crew with Vervelyn policy.
This script runs the crew directly without all the API infrastructure.
"""

import json
import os
import sys
from pathlib import Path

# Set up minimal environment
os.environ["ENVIRONMENT"] = "development"
os.environ["OPENAI_API_KEY"] = os.environ.get("OPENAI_API_KEY", "")
os.environ["API_SECRET_KEY"] = os.environ.get("API_SECRET_KEY", "test-key")

# Check for API key
if not os.environ["OPENAI_API_KEY"]:
    print("❌ Error: OPENAI_API_KEY environment variable is required")
    print("Set it with: export OPENAI_API_KEY='your-key-here'")
    sys.exit(1)

# Import what we need
try:
    from crew import MemoryMakerCrew
    print("✅ Successfully imported MemoryMakerCrew")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("\nTrying to install crewai...")
    os.system("pip install crewai==0.148.0")
    from crew import MemoryMakerCrew

def run_vervelyn_test():
    """Run the memory maker crew with Vervelyn corporate policy."""
    
    # Load the Vervelyn policy
    payload_path = Path(__file__).parent.parent.parent.parent / "sparkjar-crew-api" / "test_payloads" / "vervelyn_corporate_policy_payload.json"
    
    # Fallback to environment variable if needed
    if not payload_path.exists():
        env_path = os.getenv("VERVELYN_PAYLOAD_PATH")
        if env_path:
            payload_path = Path(env_path)
    
    with open(payload_path, 'r') as f:
        payload = json.load(f)
    
    print("\n=== Running Memory Maker Crew for Vervelyn Publishing ===\n")
    
    # Extract request data
    request_data = payload['data']
    
    print(f"Actor Type: {request_data['actor_type']} (CLIENT REALM)")
    print(f"Actor ID: {request_data['actor_id']}")
    print(f"Client ID: {request_data['client_user_id']}")
    print(f"Policy Length: {len(request_data['text_content'])} characters")
    
    # Initialize the crew
    print("\n🚀 Initializing crew...")
    crew = MemoryMakerCrew(
        client_user_id=request_data['client_user_id'],
        actor_type=request_data['actor_type'],
        actor_id=request_data['actor_id']
    )
    
    # Prepare inputs
    inputs = {
        'text_content': request_data['text_content'],
        'metadata': request_data.get('metadata', {})
    }
    
    # Run the crew
    print("\n🔄 Processing corporate policy...")
    print("This will analyze the text and create memories in the CLIENT realm.")
    print("Please wait...\n")
    
    try:
        result = crew.kickoff(inputs=inputs)
        
        print("\n✅ Crew execution completed!")
        print("\n=== Crew Output ===")
        print(result)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_vervelyn_test()