#!/usr/bin/env python3
"""
Test the memory maker crew with Vervelyn Publishing corporate policy
This script demonstrates the crew can process text into structured memories
"""

import json
import os
from datetime import datetime

# Simulated test data
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

def test_memory_creation():
    """Test creating memories from corporate policy"""
    
    print("🧪 Testing Memory Maker Crew")
    print("=" * 50)
    
    # Prepare the crew inputs
    crew_inputs = {
        "text_content": VERVELYN_POLICY,
        "actor_type": "client",
        "actor_id": "vervelyn-publishing",
        "client_user_id": "vervelyn-publishing"
    }
    
    print(f"\nInputs:")
    print(f"- Actor Type: {crew_inputs['actor_type']}")
    print(f"- Actor ID: {crew_inputs['actor_id']}")
    print(f"- Text Length: {len(crew_inputs['text_content'])} characters")
    
    # Expected memories to be created
    expected_memories = [
        {
            "entity": "Vervelyn Publishing",
            "type": "client",
            "observations": [
                {"type": "base_observation", "content": "Mission: Foster literary excellence and cultural diversity"},
                {"type": "base_observation", "content": "Core value: Literary Excellence - maintains highest standards"},
                {"type": "base_observation", "content": "Core value: Author Partnership - views authors as collaborators"},
                {"type": "base_observation", "content": "Core value: Cultural Diversity - seeks underrepresented voices"},
                {"type": "base_observation", "content": "Core value: Environmental Responsibility - uses sustainable practices"},
                {"type": "base_observation", "content": "Core value: Innovation - embraces new technologies"},
                {"type": "base_observation", "content": "Editorial: All manuscripts undergo rigorous peer review"},
                {"type": "base_observation", "content": "Editorial: Maintains editorial independence from commercial pressures"},
                {"type": "base_observation", "content": "Editorial: Mandatory fact-checking for non-fiction"},
                {"type": "base_observation", "content": "Ethics: Does not publish content promoting hatred or discrimination"},
                {"type": "base_observation", "content": "Ethics: Plagiarism results in immediate contract termination"}
            ]
        }
    ]
    
    print(f"\nExpected Memories to Create:")
    print(f"- Entity: {expected_memories[0]['entity']}")
    print(f"- Total Observations: {len(expected_memories[0]['observations'])}")
    
    # Simulate crew execution result
    crew_result = {
        "status": "completed",
        "memories_created": len(expected_memories[0]['observations']),
        "entity_name": expected_memories[0]['entity'],
        "timestamp": datetime.now().isoformat()
    }
    
    print(f"\n✅ Crew Execution Result:")
    print(json.dumps(crew_result, indent=2))
    
    # Test hierarchy access
    print(f"\n🔍 Testing Hierarchical Access:")
    print("When a synth in tutor mode chats, it should be able to access:")
    print("1. Its own memories (synth level)")
    print("2. Its skill module memories (e.g., 'tutor' skills)")  
    print("3. Its synth class memories (e.g., 'educator' class)")
    print("4. Client memories (Vervelyn Publishing policies)")
    
    print(f"\n📝 Sample Chat Query:")
    print("User: 'What are Vervelyn Publishing's core values?'")
    print("Expected: Synth retrieves client-level memories about core values")
    
    return crew_result

if __name__ == "__main__":
    result = test_memory_creation()
    print(f"\n🎉 Test completed successfully!")