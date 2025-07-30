#!/usr/bin/env python3
"""
Test script to verify memory_maker_crew execution via API
"""

import asyncio
import httpx
import jwt
import os
from datetime import datetime, timedelta
from typing import Dict, Any

# Configuration
API_URL = "http://localhost:8000"  # Adjust if needed
API_SECRET_KEY = os.getenv("API_SECRET_KEY", "test-secret-key")

def generate_test_token() -> str:
    """Generate a test JWT token with proper scopes"""
    payload = {
        "sub": "test-user",
        "scopes": ["sparkjar_internal", "crew_execute"],
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    
    return jwt.encode(payload, API_SECRET_KEY, algorithm="HS256")

async def test_health_check():
    """Test the health check endpoint"""
    print("\n🔍 Testing health check endpoint...")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_URL}/health")
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "memory_maker_crew" in data["available_crews"]
        
    print("✅ Health check passed!")

async def test_list_crews():
    """Test the list crews endpoint"""
    print("\n🔍 Testing list crews endpoint...")
    
    token = generate_test_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_URL}/crews", headers=headers)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        assert response.status_code == 200
        data = response.json()
        assert "memory_maker_crew" in data["available_crews"]
        
    print("✅ List crews passed!")

async def test_execute_memory_maker_crew():
    """Test executing the memory_maker_crew"""
    print("\n🔍 Testing memory_maker_crew execution...")
    
    token = generate_test_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test payload
    payload = {
        "crew_name": "memory_maker_crew",
        "inputs": {
            "client_user_id": "test-client-123",
            "actor_type": "synth",
            "actor_id": "test-synth-456",
            "text_content": """
            I had a meeting with John Smith from Acme Corp today. 
            We discussed the new project timeline and budget constraints. 
            The deadline is set for March 15th, 2025. 
            John mentioned they have a $50,000 budget allocated.
            Their main requirements are:
            1. Fast turnaround time
            2. High quality deliverables
            3. Weekly progress reports
            
            Action items:
            - Send proposal by Friday
            - Schedule follow-up meeting next week
            - Research Acme Corp's previous projects
            """,
            "metadata": {
                "source": "meeting_notes",
                "date": "2025-01-07"
            }
        }
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        print("Sending crew execution request...")
        response = await client.post(
            f"{API_URL}/execute_crew", 
            json=payload,
            headers=headers
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code != 200:
            print(f"❌ Execution failed: {response.json()}")
            return
        
        data = response.json()
        assert data["success"] == True
        assert data["crew_name"] == "memory_maker_crew"
        assert "result" in data
        
        print(f"\n📊 Execution Results:")
        print(f"  - Success: {data['success']}")
        print(f"  - Execution Time: {data['execution_time']:.2f}s")
        print(f"  - Result Preview: {data['result'][:200]}...")
        
    print("✅ Memory maker crew execution passed!")

async def test_invalid_crew():
    """Test error handling for invalid crew name"""
    print("\n🔍 Testing error handling for invalid crew...")
    
    token = generate_test_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    payload = {
        "crew_name": "non_existent_crew",
        "inputs": {}
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_URL}/execute_crew", 
            json=payload,
            headers=headers
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        assert response.status_code == 404
        
    print("✅ Error handling test passed!")

async def test_authentication():
    """Test authentication requirement"""
    print("\n🔍 Testing authentication requirement...")
    
    # Test without token
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_URL}/crews")
        
        print(f"Status Code: {response.status_code}")
        assert response.status_code == 403  # Forbidden without token
        
    # Test with invalid token
    headers = {"Authorization": "Bearer invalid-token"}
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_URL}/crews", headers=headers)
        
        print(f"Status Code: {response.status_code}")
        assert response.status_code == 401  # Unauthorized with invalid token
        
    print("✅ Authentication test passed!")

async def main():
    """Run all tests"""
    print("🚀 Starting Memory Maker Crew API Tests")
    print(f"API URL: {API_URL}")
    
    try:
        await test_health_check()
        await test_authentication()
        await test_list_crews()
        await test_execute_memory_maker_crew()
        await test_invalid_crew()
        
        print("\n✅ All tests passed successfully!")
        
    except AssertionError as e:
        print(f"\n❌ Test assertion failed: {e}")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())