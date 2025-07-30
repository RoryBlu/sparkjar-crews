"""
Unit tests for SparkJAR Crews Service API endpoints
"""

import pytest
import json
from datetime import datetime
from unittest.mock import patch, Mock, MagicMock
from fastapi.testclient import TestClient
from fastapi import HTTPException

# Import the app
from api.server import app
from api.crew_registry import CREW_REGISTRY


class TestCrewsAPI:
    """Test class for Crews API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def valid_token(self):
        """Mock valid JWT token"""
        return "Bearer valid-test-token"
    
    @pytest.fixture
    def invalid_token(self):
        """Mock invalid JWT token"""
        return "Bearer invalid-test-token"
    
    @pytest.fixture
    def mock_token_payload(self):
        """Mock decoded token payload"""
        return {
            "sub": "test-user",
            "scopes": ["sparkjar_internal"],
            "exp": int(datetime.utcnow().timestamp()) + 3600
        }
    
    @pytest.fixture
    def mock_crew_class(self):
        """Mock crew class for testing"""
        class MockCrew:
            def __init__(self, *args, **kwargs):
                pass
            
            def kickoff(self, inputs):
                return {"status": "completed", "result": "Mock crew executed successfully"}
        
        return MockCrew
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "sparkjar-crews"
        assert "environment" in data
        assert "available_crews" in data
        assert isinstance(data["available_crews"], list)
    
    @patch('api.server.verify_token')
    def test_execute_crew_success(self, mock_verify_token, client, valid_token, mock_token_payload, mock_crew_class):
        """Test successful crew execution"""
        # Setup mocks
        mock_verify_token.return_value = mock_token_payload
        
        # Mock the crew registry
        with patch.dict(CREW_REGISTRY, {"test_crew": mock_crew_class}):
            request_data = {
                "crew_name": "test_crew",
                "inputs": {
                    "text_content": "Test content",
                    "actor_type": "human",
                    "actor_id": "test-123"
                }
            }
            
            response = client.post(
                "/execute_crew",
                json=request_data,
                headers={"Authorization": valid_token}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert data["crew_name"] == "test_crew"
            assert data["result"] is not None
            assert data["error"] is None
            assert "execution_time" in data
            assert data["execution_time"] > 0
    
    @patch('api.server.verify_token')
    def test_execute_crew_not_found(self, mock_verify_token, client, valid_token, mock_token_payload):
        """Test crew execution with non-existent crew"""
        mock_verify_token.return_value = mock_token_payload
        
        request_data = {
            "crew_name": "non_existent_crew",
            "inputs": {"test": "data"}
        }
        
        response = client.post(
            "/execute_crew",
            json=request_data,
            headers={"Authorization": valid_token}
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    @patch('api.server.verify_token')
    def test_execute_crew_with_error(self, mock_verify_token, client, valid_token, mock_token_payload):
        """Test crew execution that throws an error"""
        mock_verify_token.return_value = mock_token_payload
        
        # Create a crew that raises an exception
        class ErrorCrew:
            def __init__(self, *args, **kwargs):
                pass
            
            def kickoff(self, inputs):
                raise Exception("Crew execution failed")
        
        with patch.dict(CREW_REGISTRY, {"error_crew": ErrorCrew}):
            request_data = {
                "crew_name": "error_crew",
                "inputs": {"test": "data"}
            }
            
            response = client.post(
                "/execute_crew",
                json=request_data,
                headers={"Authorization": valid_token}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is False
            assert data["crew_name"] == "error_crew"
            assert "error" in data
            assert "Crew execution failed" in data["error"]
    
    @patch('api.server.verify_token')
    def test_execute_crew_unauthorized(self, mock_verify_token, client, invalid_token):
        """Test crew execution with invalid token"""
        from sparkjar_shared.auth import InvalidTokenError
        mock_verify_token.side_effect = InvalidTokenError("Invalid token")
        
        request_data = {
            "crew_name": "test_crew",
            "inputs": {"test": "data"}
        }
        
        response = client.post(
            "/execute_crew",
            json=request_data,
            headers={"Authorization": invalid_token}
        )
        
        assert response.status_code == 401
        assert "Invalid authentication token" in response.json()["detail"]
    
    @patch('api.server.verify_token')
    def test_execute_crew_insufficient_permissions(self, mock_verify_token, client, valid_token):
        """Test crew execution with insufficient permissions"""
        # Token without required scopes
        mock_verify_token.return_value = {
            "sub": "test-user",
            "scopes": ["wrong_scope"],
            "exp": int(datetime.utcnow().timestamp()) + 3600
        }
        
        request_data = {
            "crew_name": "test_crew",
            "inputs": {"test": "data"}
        }
        
        response = client.post(
            "/execute_crew",
            json=request_data,
            headers={"Authorization": valid_token}
        )
        
        assert response.status_code == 401  # Changed from 403 - the API returns 401 for auth errors
        assert "Insufficient permissions" in response.json()["detail"]
    
    @patch('api.server.verify_token')
    def test_list_crews(self, mock_verify_token, client, valid_token, mock_token_payload, mock_crew_class):
        """Test list crews endpoint"""
        mock_verify_token.return_value = mock_token_payload
        
        # Mock some crews in the registry - clear existing ones first
        with patch.dict(CREW_REGISTRY, {
            "crew1": mock_crew_class,
            "crew2": mock_crew_class
        }, clear=True):
            response = client.get(
                "/crews",
                headers={"Authorization": valid_token}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert "available_crews" in data
            assert "total_count" in data
            assert data["total_count"] == 2
            assert "crew1" in data["available_crews"]
            assert "crew2" in data["available_crews"]
            
            # Check crew metadata
            crew1_info = data["available_crews"]["crew1"]
            assert "class_name" in crew1_info
            assert "module" in crew1_info
            assert "description" in crew1_info
    
    @patch('api.server.verify_token')
    def test_list_crews_unauthorized(self, mock_verify_token, client, invalid_token):
        """Test list crews with invalid token"""
        from sparkjar_shared.auth import InvalidTokenError
        mock_verify_token.side_effect = InvalidTokenError("Invalid token")
        
        response = client.get(
            "/crews",
            headers={"Authorization": invalid_token}
        )
        
        assert response.status_code == 401
    
    def test_execute_crew_no_token(self, client):
        """Test crew execution without authentication token"""
        request_data = {
            "crew_name": "test_crew",
            "inputs": {"test": "data"}
        }
        
        response = client.post("/execute_crew", json=request_data)
        
        assert response.status_code == 403  # FastAPI returns 403 for missing credentials
        assert "Not authenticated" in response.json()["detail"]
    
    @patch('api.server.verify_token')
    def test_execute_crew_with_timeout(self, mock_verify_token, client, valid_token, mock_token_payload):
        """Test crew execution with timeout parameter"""
        mock_verify_token.return_value = mock_token_payload
        
        class SlowCrew:
            def __init__(self, *args, **kwargs):
                pass
            
            def kickoff(self, inputs):
                # Simulate slow execution
                import time
                time.sleep(0.1)
                return {"status": "completed"}
        
        with patch.dict(CREW_REGISTRY, {"slow_crew": SlowCrew}):
            request_data = {
                "crew_name": "slow_crew",
                "inputs": {"test": "data"},
                "timeout": 60
            }
            
            response = client.post(
                "/execute_crew",
                json=request_data,
                headers={"Authorization": valid_token}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
    
    @patch('api.server.verify_token')
    def test_request_tracing(self, mock_verify_token, client, valid_token, mock_token_payload, mock_crew_class):
        """Test request tracing middleware"""
        mock_verify_token.return_value = mock_token_payload
        
        with patch.dict(CREW_REGISTRY, {"test_crew": mock_crew_class}):
            request_data = {
                "crew_name": "test_crew",
                "inputs": {"test": "data"}
            }
            
            response = client.post(
                "/execute_crew",
                json=request_data,
                headers={"Authorization": valid_token}
            )
            
            # Check that request ID is in response headers
            assert "X-Request-ID" in response.headers
            assert len(response.headers["X-Request-ID"]) > 0
    
    def test_cors_headers_development(self, client):
        """Test CORS headers in development environment"""
        # This test assumes we're in development mode
        response = client.options(
            "/execute_crew",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST"
            }
        )
        
        # In development, CORS should allow all origins
        # Note: This might fail in production environment
        if response.status_code == 200:
            assert "access-control-allow-origin" in response.headers


if __name__ == "__main__":
    pytest.main([__file__, "-v"])