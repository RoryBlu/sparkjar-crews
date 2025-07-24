#!/usr/bin/env python3
"""
Minimal test to demonstrate proper realm categorization for Vervelyn corporate policy.
This version shows the conceptual flow without running the actual crew.
"""

import json

def analyze_vervelyn_policy():
    """Analyze the Vervelyn corporate policy to show proper realm categorization."""
    
    # Load the test payload
    payload_path = "/Users/r.t.rawlings/sparkjar-crew/_reorg/sparkjar-crew-api/test_payloads/vervelyn_corporate_policy_payload.json"
    
    with open(payload_path, 'r') as f:
        payload = json.load(f)
    
    print("=== Vervelyn Corporate Policy Analysis ===\n")
    
    # Extract the request data
    request_data = payload['data']
    
    print(f"✅ Actor Type: {request_data['actor_type']} (CLIENT REALM)")
    print(f"✅ Actor ID: {request_data['actor_id']}")
    print(f"✅ Client User ID: {request_data['client_user_id']}")
    print(f"✅ Text Length: {len(request_data['text_content'])} characters")
    
    # Parse the policy content
    content = request_data['text_content']
    
    print("\n=== Content Analysis for Memory Categorization ===\n")
    
    # Examples of what should be extracted as CLIENT REALM memories
    client_memories = [
        {
            "entity": "synth_disclosure_policy",
            "type": "policy",
            "observation": "When a synthetic human is the author or spokesperson, communications must identify this fact openly",
            "realm": "CLIENT",
            "reason": "Company-specific policy that overrides default behavior"
        },
        {
            "entity": "memory_curation_principle", 
            "type": "policy",
            "observation": "Only the most relevant, current, and actionable information is kept 'top of mind' for all employees",
            "realm": "CLIENT",
            "reason": "Vervelyn's specific approach to memory management"
        },
        {
            "entity": "crisis_response_policy",
            "type": "procedure",
            "observation": "Only designated executives may respond publicly to controversy; synths must escalate",
            "realm": "CLIENT", 
            "reason": "Company-specific crisis management procedure"
        },
        {
            "entity": "quarterly_review_cycle",
            "type": "procedure",
            "observation": "Policy will be reviewed quarterly by the executive team",
            "realm": "CLIENT",
            "reason": "Vervelyn's specific review schedule"
        }
    ]
    
    print("CLIENT REALM Memories (Company Policies):")
    print("-" * 50)
    for i, memory in enumerate(client_memories, 1):
        print(f"\n{i}. Entity: {memory['entity']}")
        print(f"   Type: {memory['type']}")
        print(f"   Observation: {memory['observation']}")
        print(f"   Why CLIENT realm: {memory['reason']}")
    
    # Examples of what would NOT be client memories
    print("\n\n❌ What This is NOT:")
    print("-" * 50)
    
    not_client = [
        {
            "example": "How to write professional communications",
            "realm": "SYNTH_CLASS",
            "reason": "This is core knowledge for any communications professional"
        },
        {
            "example": "How to use Slack or Teams",
            "realm": "SKILL_MODULE", 
            "reason": "This is tool-specific knowledge"
        },
        {
            "example": "Bob prefers formal language",
            "realm": "SYNTH",
            "reason": "This would be a personal preference of an individual synth"
        }
    ]
    
    for item in not_client:
        print(f"\n- \"{item['example']}\"")
        print(f"  Would belong to: {item['realm']} realm")
        print(f"  Because: {item['reason']}")
    
    print("\n\n=== Key Insight ===")
    print("The Vervelyn policy contains CLIENT REALM knowledge because it defines:")
    print("1. Company-specific rules that override default behaviors")
    print("2. Organizational procedures unique to Vervelyn")
    print("3. Policies that ALL synths at Vervelyn must follow")
    print("4. Not general knowledge, but Vervelyn's way of doing things")
    
    print("\n=== Memory Storage Pattern ===")
    print("When the Memory Maker Crew processes this:")
    print("- Actor Type: 'client' ✅ (correctly identified)")
    print("- Actor ID: matches client_id ✅ (proper client context)")
    print("- Result: All memories stored in CLIENT REALM")
    print("- Effect: These policies override any default synth_class or skill_module behaviors")

if __name__ == "__main__":
    analyze_vervelyn_policy()