#!/usr/bin/env python3
"""
Test the memory maker crew with Vervelyn Publishing corporate policy
This creates a complete test harness for the crew execution
"""

import json
import os
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Check for required environment variables
if not os.getenv("OPENAI_API_KEY"):
    print("❌ Error: OPENAI_API_KEY not set in environment")
    print("Please set it in your .env file or export it")
    sys.exit(1)

VERVELYN_POLICY = """
Vervelyn Publishing Corporate Policy

Mission Statement:
Vervelyn Publishing is committed to fostering literary excellence and cultural diversity through the publication of high-quality fiction and non-fiction works. We believe in the transformative power of stories and ideas to inspire, educate, and connect people across boundaries.

Core Values:
1. Literary Excellence: We maintain the highest standards in editorial quality and production values
2. Author Partnership: We view our authors as partners and collaborators in the creative process
3. Cultural Diversity: We actively seek voices from underrepresented communities
4. Environmental Responsibility: We use sustainable practices in all aspects of our operations
5. Innovation: We embrace new technologies while honoring traditional publishing values

Editorial Guidelines:
- All manuscripts undergo rigorous peer review
- We maintain editorial independence from commercial pressures
- Fact-checking is mandatory for all non-fiction works
- We respect author voice while ensuring clarity and accessibility

Employee Conduct:
- Professional integrity is paramount
- Confidentiality of manuscripts and author information must be maintained
- Conflicts of interest must be disclosed
- Respectful workplace behavior is mandatory

Publishing Ethics:
- We do not publish content that promotes hatred or discrimination
- Plagiarism results in immediate contract termination
- We support fair use and proper attribution
- Author rights are clearly defined in all contracts
"""

def test_memory_maker_crew():
    """Test the memory maker crew with Vervelyn Publishing policy"""
    
    print("🚀 Testing Memory Maker Crew with Vervelyn Publishing Policy")
    print("=" * 60)
    
    try:
        # Import the crew
        from crews.memory_maker_crew.crew import MemoryMakerCrew
        
        print("✅ Successfully imported MemoryMakerCrew")
        
        # Create crew instance
        crew = MemoryMakerCrew()
        print("✅ Created crew instance")
        
        # Prepare inputs
        inputs = {
            "text_content": VERVELYN_POLICY,
            "actor_type": "client",
            "actor_id": "vervelyn-publishing",
            "client_user_id": "vervelyn-publishing"
        }
        
        print(f"\n📋 Inputs:")
        print(f"  - Actor Type: {inputs['actor_type']}")
        print(f"  - Actor ID: {inputs['actor_id']}")
        print(f"  - Text Length: {len(inputs['text_content'])} characters")
        
        print(f"\n🔄 Running crew (this may take a moment)...")
        
        # Execute the crew
        result = crew.kickoff(inputs=inputs)
        
        print(f"\n✅ Crew execution completed!")
        print(f"\n📊 Results:")
        print("-" * 60)
        
        # Display the result
        if hasattr(result, 'raw'):
            print(result.raw)
        else:
            print(str(result))
        
        # Save results to file
        output_file = "vervelyn_memory_results.json"
        with open(output_file, 'w') as f:
            json.dump({
                "inputs": inputs,
                "result": str(result),
                "success": True
            }, f, indent=2)
        
        print(f"\n💾 Results saved to: {output_file}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("Make sure you're in the correct directory and dependencies are installed")
        return False
    except Exception as e:
        print(f"❌ Error during execution: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    success = test_memory_maker_crew()
    
    if success:
        print(f"\n🎉 Test completed successfully!")
        print(f"\n📝 Next Steps:")
        print("1. Check vervelyn_memory_results.json for detailed results")
        print("2. The memories should now be available in the memory service")
        print("3. A synth in 'tutor' mode should be able to access these client-level memories")
    else:
        print(f"\n❌ Test failed. Please check the errors above.")
        sys.exit(1)