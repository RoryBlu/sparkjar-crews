#!/usr/bin/env python
"""
Direct execution script for testing the Memory Maker Crew.
This allows testing the crew without running the full API server.
"""
import os
import sys
import json
import asyncio
from pathlib import Path

# Add paths for imports
current_dir = Path(__file__).parent
crews_dir = current_dir.parent
sparkjar_crews_dir = crews_dir.parent

sys.path.insert(0, str(sparkjar_crews_dir))
sys.path.insert(0, str(current_dir))

# Set up environment
os.environ["ENVIRONMENT"] = os.environ.get("ENVIRONMENT", "development")

# Now we can import the handler
from memory_maker_crew_handler import MemoryMakerCrewHandler

async def main():
    """Test the memory maker crew with Vervelyn Publishing corporate policy."""
    print("🚀 Testing Memory Maker Crew directly...")
    
    # Load the test payload
    # Use relative path from the crew location
    base_path = Path(__file__).parent.parent.parent.parent
    payload_path = base_path / "sparkjar-crew-api" / "test_payloads" / "vervelyn_corporate_policy_payload.json"
    
    # Fallback to environment variable if needed
    if not payload_path.exists():
        env_path = os.getenv("VERVELYN_PAYLOAD_PATH")
        if env_path:
            payload_path = Path(env_path)
    
    if not payload_path.exists():
        print(f"❌ Test payload not found at: {payload_path}")
        return
    
    with open(payload_path, 'r') as f:
        payload = json.load(f)
    
    print(f"📄 Loaded payload for {payload['actor_type']} actor: {payload['actor_id']}")
    
    # Extract the request data
    request_data = {
        "client_user_id": payload["client_user_id"],
        "actor_type": payload["actor_type"],
        "actor_id": payload["actor_id"],
        **payload["data"]
    }
    
    # Create and execute the crew
    handler = MemoryMakerCrewHandler()
    
    try:
        print("\n🔄 Executing crew...")
        result = await handler.execute(request_data)
        
        print("\n✅ Crew execution completed!")
        print("\n📊 Results:")
        print(json.dumps(result, indent=2))
        
        # Check if memories were created
        if "created_memories" in result:
            memory_count = len(result["created_memories"])
            print(f"\n💾 Created {memory_count} memories")
            
            # Show a sample of created memories
            for i, memory in enumerate(result["created_memories"][:3]):
                print(f"\nMemory {i+1}:")
                print(f"  Entity: {memory.get('entity_name', 'N/A')}")
                print(f"  Type: {memory.get('entity_type', 'N/A')}")
                if 'observations' in memory and memory['observations']:
                    print(f"  Observations: {len(memory['observations'])}")
                    for obs in memory['observations'][:2]:
                        print(f"    - {obs.get('observation_type', 'N/A')}: {obs.get('observation', 'N/A')[:100]}...")
        
    except Exception as e:
        print(f"\n❌ Error executing crew: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())