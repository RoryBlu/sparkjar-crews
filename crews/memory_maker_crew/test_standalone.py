#!/usr/bin/env python3
"""
Standalone test for Memory Maker Crew - runs the crew directly without handlers.
"""

import os
import json
import sys
from pathlib import Path
from dotenv import load_dotenv

# Set up the path
current_dir = Path(__file__).parent
crews_dir = current_dir.parent.parent
sys.path.insert(0, str(crews_dir))

# Load environment variables
env_file = crews_dir / '.env'
if env_file.exists():
    load_dotenv(env_file)
    print(f"✅ Loaded .env from {env_file}")

# Set PYTHONPATH to include tools directory
os.environ['PYTHONPATH'] = str(crews_dir)

# Now import the crew
from crew import MemoryMakerCrew

def test_vervelyn():
    """Run the Memory Maker Crew with Vervelyn policy data."""
    
    # Check environment
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not found. Please set it in .env file")
        return
    print("✅ OPENAI_API_KEY is set")
    
    if not os.getenv("API_SECRET_KEY"):
        os.environ["API_SECRET_KEY"] = "test-key-for-local-run"
        print("⚠️  Using test API_SECRET_KEY")
    
    # Load test data
    payload_file = "/Users/r.t.rawlings/sparkjar-crew/_reorg/sparkjar-crew-api/test_payloads/vervelyn_corporate_policy_payload.json"
    
    with open(payload_file, 'r') as f:
        payload = json.load(f)
    
    # Extract data
    data = payload['data']
    
    print("\n=== Vervelyn Corporate Policy Test ===")
    print(f"Actor Type: {data['actor_type']}")
    print(f"Actor ID: {data['actor_id']}")
    print(f"Client ID: {data['client_user_id']}")
    print(f"Text Length: {len(data['text_content'])} chars")
    print(f"Text Preview: {data['text_content'][:150]}...")
    
    # Initialize crew
    print("\n🚀 Initializing Memory Maker Crew...")
    crew = MemoryMakerCrew(
        client_user_id=data['client_user_id'],
        actor_type=data['actor_type'],
        actor_id=data['actor_id']
    )
    
    # Prepare inputs
    inputs = {
        'text_content': data['text_content'],
        'actor_type': data['actor_type'],
        'actor_id': data['actor_id'],
        'client_user_id': data['client_user_id']
    }
    
    print("\n🔄 Running crew (this may take 1-2 minutes)...")
    
    try:
        # Execute the crew
        result = crew.kickoff(inputs=inputs)
        
        print("\n✅ Success! Crew execution completed.")
        
        # Display output
        print("\n=== Crew Output ===")
        if hasattr(result, 'output'):
            output = result.output
            if isinstance(output, str):
                # Try to parse as JSON for better display
                try:
                    output_data = json.loads(output)
                    print(json.dumps(output_data, indent=2))
                except:
                    print(output)
            else:
                print(output)
        else:
            print(str(result))
        
        # Show task results if available
        if hasattr(result, 'tasks_output'):
            print("\n=== Task Results ===")
            for i, task_output in enumerate(result.tasks_output):
                print(f"\nTask {i+1}:")
                if hasattr(task_output, 'description'):
                    print(f"Description: {task_output.description}")
                if hasattr(task_output, 'output'):
                    print(f"Output: {str(task_output.output)[:200]}...")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Change to crew directory for relative imports to work
    os.chdir(current_dir)
    test_vervelyn()