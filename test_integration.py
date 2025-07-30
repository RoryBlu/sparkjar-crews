#!/usr/bin/env python
"""
Simple integration test for the Crews API
"""

from fastapi.testclient import TestClient
from api.server import app
from sparkjar_shared.auth import create_token
from datetime import timedelta

def test_integration():
    """Test basic API functionality"""
    client = TestClient(app)
    
    # Test health check
    print("Testing health check...")
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    print(f"✅ Health check passed: {data['status']}")
    print(f"Available crews: {data['available_crews']}")
    
    # Create a valid token
    token = create_token(
        subject="test-service",
        scopes=["sparkjar_internal", "crew_execute"],
        expires_delta=timedelta(hours=1)
    )
    
    # Test crew listing
    print("\nTesting crew listing...")
    response = client.get(
        "/crews",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    print(f"✅ Crew listing passed: {data['total_count']} crews available")
    
    # Test crew execution (without actually running a crew)
    print("\nTesting crew execution endpoint...")
    response = client.post(
        "/execute_crew",
        json={
            "crew_name": "nonexistent_crew",
            "inputs": {"test": "data"}
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404  # Should fail for nonexistent crew
    print("✅ Crew execution endpoint properly validates crew existence")
    
    # Test authentication
    print("\nTesting authentication...")
    response = client.post(
        "/execute_crew",
        json={
            "crew_name": "memory_maker_crew",
            "inputs": {"test": "data"}
        }
        # No authorization header
    )
    assert response.status_code == 403  # FastAPI HTTPBearer returns 403 for missing auth
    print("✅ Authentication properly required")
    
    print("\n🎉 All integration tests passed!")

if __name__ == "__main__":
    test_integration()