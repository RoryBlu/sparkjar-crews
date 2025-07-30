#!/usr/bin/env python3
"""
Test script to run Memory Maker Crew with Vervelyn corporate policy data.
"""

import json
import os
import sys
import asyncio
from pathlib import Path

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from crews.memory_maker_crew.memory_maker_crew_handler import MemoryMakerCrewHandler
from crews.memory_maker_crew.models import MemoryMakerRequest

async def test_vervelyn_policy():
    """Test the Memory Maker Crew with Vervelyn corporate policy."""
    
    # Load the test payload
    # Use relative path from the crew location
    base_path = Path(__file__).parent.parent.parent.parent
    payload_path = base_path / "sparkjar-crew-api" / "test_payloads" / "vervelyn_corporate_policy_payload.json"
    
    # Fallback to environment variable or absolute path if needed
    if not payload_path.exists():
        env_path = os.getenv("VERVELYN_PAYLOAD_PATH")
        if env_path:
            payload_path = Path(env_path)
        else:
            # Last resort: try the absolute path
            payload_path = Path("/Users/r.t.rawlings/sparkjar-crew/_reorg/sparkjar-crew-api/test_payloads/vervelyn_corporate_policy_payload.json")
    
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
    
    # Validate the request using Pydantic model
    try:
        validated_request = MemoryMakerRequest(**request_data)
        print("\n✅ Request validation passed!")
    except Exception as e:
        print(f"\n❌ Request validation failed: {e}")
        return
    
    # Initialize the crew handler
    print("\n🚀 Initializing Memory Maker Crew...")
    handler = MemoryMakerCrewHandler()
    
    # Execute the crew
    print("\n🔄 Processing text and extracting memories...")
    print("This may take a few minutes...\n")
    
    try:
        result = await handler.execute(request_data)
        
        print("\n✅ Crew execution completed!")
        print(f"\nStatus: {result.get('status', 'unknown')}")
        
        # Display results
        if 'result' in result:
            crew_output = result['result']
            print("\n=== Crew Output ===")
            if isinstance(crew_output, dict):
                print(json.dumps(crew_output, indent=2))
            else:
                print(crew_output)
        
        # Display metadata
        if 'metadata' in result:
            print("\n=== Processing Metadata ===")
            metadata = result['metadata']
            print(f"Processing Time: {metadata.get('processing_time_seconds', 'N/A')} seconds")
            print(f"Text Length: {metadata.get('text_length', 'N/A')} characters")
            print(f"Execution ID: {metadata.get('crew_execution_id', 'N/A')}")
        
        # Display any errors
        if 'errors' in result and result['errors']:
            print("\n⚠️  Errors encountered:")
            for error in result['errors']:
                print(f"  - {error}")
                
    except Exception as e:
        print(f"\n❌ Crew execution failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Set up environment variables if needed
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Warning: OPENAI_API_KEY not set in environment")
    
    if not os.getenv("API_SECRET_KEY"):
        print("⚠️  Warning: API_SECRET_KEY not set in environment")
        print("Setting a test API_SECRET_KEY...")
        os.environ["API_SECRET_KEY"] = "test-secret-key-for-local-testing"
    
    # Run the test
    asyncio.run(test_vervelyn_policy())