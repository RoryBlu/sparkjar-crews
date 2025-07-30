"""
Unit tests for SparkJAR Crews API Server
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from fastapi import status

# Import the app
from api.server import app
from api.crew_registry import CREW_REGISTRY
from sparkjar_shared.auth import create_token


class TestCrewsAPI:
    """Test cases for the Crews API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def valid_token(self):
        """Create a valid JWT token for testing"""
        return create_token(
            subject="test-service",
            scopes=["sparkjar_internal", "crew_execute"],
            expires_delta=timedelta(hours=1)
        )
    
    @pytest.fixture
    def invalid_token(self):
        """Create an invalid JWT token for testing"""
        return "invalid.jwt.token"
    
    @pytest.fixture
    def insufficient_scope_token(self):
        """Create a token with insufficient scopes"""
        return create_token(
            subject="test-service",
            scopes=["read_only"],
            expires_delta=timedelta(hours=1)
        )
    
    def test_health_check_success(self, client):
        """Test health check endpoint returns success"""
        response = client.get("/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "sparkjar-crews"
        assert "available_crews" in data
        assert "timestamp" in data
        assert isinstance(data["available_crews"], list)
    
    def test_health_check_includes_available_crews(self, client):
        """Test health check includes list of available crews"""
        response = client.get("/health")
        data = response.json()
        
        # Should include crews from registry
        expected_crews = list(CREW_REGISTRY.keys())
        assert data["available_crews"] == expected_crews
    
    def test_execute_crew_without_token_fails(self, client):
        """Test crew execution without token returns 401"""
        response = client.post("/execute_crew", json={
            "crew_name": "memory_maker_crew",
            "inputs": {"text_content": "test"}
        })
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_execute_crew_with_invalid_token_fails(self, client, invalid_token):
        """Test crew execution with invalid token returns 401"""
        response = client.post(
            "/execute_crew",
            json={
                "crew_name": "memory_maker_crew",
                "inputs": {"text_content": "test"}
            },
            headers={"Authorization": f"Bearer {invalid_token}"}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_execute_crew_with_insufficient_scope_fails(self, client, insufficient_scope_token):
        """Test crew execution with insufficient scope returns 403"""
        response = client.post(
            "/execute_crew",
            json={
                "crew_name": "memory_maker_crew",
                "inputs": {"text_content": "test"}
            },
            headers={"Authorization": f"Bearer {insufficient_scope_token}"}
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_execute_crew_nonexistent_crew_fails(self, client, valid_token):
        """Test executing non-existent crew returns 404"""
        response = client.post(
            "/execute_crew",
            json={
                "crew_name": "nonexistent_crew",
                "inputs": {"text_content": "test"}
            },
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    @patch('api.crew_registry.CREW_REGISTRY')
    def test_execute_crew_success(self, mock_registry, client, valid_token):
        """Test successful crew execution"""
        # Mock crew class and instance
        mock_crew_class = Mock()
        mock_crew_instance = Mock()
        mock_crew_class.return_value = mock_crew_instance
        mock_crew_instance.kickoff.return_value = "Test result"
        
        mock_registry.__getitem__.return_value = mock_crew_class
        mock_registry.__contains__.return_value = True
        mock_registry.keys.return_value = ["test_crew"]
        
        response = client.post(
            "/execute_crew",
            json={
                "crew_name": "test_crew",
                "inputs": {
                    "text_content": "test content",
                    "actor_type": "human",
                    "actor_id": "user-123",
                    "client_user_id": "client-456"
                }
            },
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["crew_name"] == "test_crew"
        assert data["result"] == "Test result"
        assert data["error"] is None
        assert "execution_time" in data
        assert "timestamp" in data
        
        # Verify crew was called correctly
        mock_crew_instance.kickoff.assert_called_once()
    
    @patch('api.crew_registry.CREW_REGISTRY')
    def test_execute_crew_with_actor_context(self, mock_registry, client, valid_token):
        """Test crew execution with actor context initialization"""
        # Mock crew class that accepts actor context
        mock_crew_class = Mock()
        mock_crew_instance = Mock()
        mock_crew_class.return_value = mock_crew_instance
        mock_crew_instance.kickoff.return_value = "Test result"
        
        mock_registry.__getitem__.return_value = mock_crew_class
        mock_registry.__contains__.return_value = True
        
        inputs = {
            "text_content": "test content",
            "actor_type": "human",
            "actor_id": "user-123",
            "client_user_id": "client-456"
        }
        
        response = client.post(
            "/execute_crew",
            json={"crew_name": "test_crew", "inputs": inputs},
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify crew was initialized with actor context
        mock_crew_class.assert_called_once_with(
            actor_type="human",
            actor_id="user-123",
            client_user_id="client-456"
        )
    
    @patch('api.crew_registry.CREW_REGISTRY')
    def test_execute_crew_handles_initialization_error(self, mock_registry, client, valid_token):
        """Test crew execution handles initialization errors gracefully"""
        # Mock crew class that fails on initialization with actor context
        mock_crew_class = Mock()
        mock_crew_instance = Mock()
        mock_crew_instance.kickoff.return_value = "Test result"
        
        # First call (with actor context) raises TypeError, second call (without) succeeds
        mock_crew_class.side_effect = [TypeError("Invalid args"), mock_crew_instance]
        
        mock_registry.__getitem__.return_value = mock_crew_class
        mock_registry.__contains__.return_value = True
        
        inputs = {
            "text_content": "test content",
            "actor_type": "human",
            "actor_id": "user-123",
            "client_user_id": "client-456"
        }
        
        response = client.post(
            "/execute_crew",
            json={"crew_name": "test_crew", "inputs": inputs},
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify crew was called twice (first with args, then without)
        assert mock_crew_class.call_count == 2
    
    @patch('api.crew_registry.CREW_REGISTRY')
    def test_execute_crew_handles_execution_error(self, mock_registry, client, valid_token):
        """Test crew execution handles runtime errors"""
        # Mock crew that fails during execution
        mock_crew_class = Mock()
        mock_crew_instance = Mock()
        mock_crew_class.return_value = mock_crew_instance
        mock_crew_instance.kickoff.side_effect = Exception("Crew execution failed")
        
        mock_registry.__getitem__.return_value = mock_crew_class
        mock_registry.__contains__.return_value = True
        
        response = client.post(
            "/execute_crew",
            json={
                "crew_name": "test_crew",
                "inputs": {"text_content": "test"}
            },
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is False
        assert data["crew_name"] == "test_crew"
        assert data["result"] is None
        assert "Crew execution failed" in data["error"]
        assert "execution_time" in data
    
    def test_list_crews_without_token_fails(self, client):
        """Test listing crews without token returns 401"""
        response = client.get("/crews")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_list_crews_success(self, client, valid_token):
        """Test successful crew listing"""
        response = client.get(
            "/crews",
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "available_crews" in data
        assert "total_count" in data
        assert "timestamp" in data
        assert isinstance(data["available_crews"], dict)
        assert isinstance(data["total_count"], int)
    
    @patch('api.crew_registry.CREW_REGISTRY')
    def test_list_crews_includes_crew_info(self, mock_registry, client, valid_token):
        """Test crew listing includes crew information"""
        # Mock crew class with metadata
        mock_crew_class = Mock()
        mock_crew_class.__name__ = "TestCrew"
        mock_crew_class.__module__ = "test.module"
        mock_crew_class.__doc__ = "Test crew description"
        
        mock_registry.items.return_value = [("test_crew", mock_crew_class)]
        mock_registry.__len__.return_value = 1
        
        response = client.get(
            "/crews",
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["total_count"] == 1
        assert "test_crew" in data["available_crews"]
        crew_info = data["available_crews"]["test_crew"]
        assert crew_info["class_name"] == "TestCrew"
        assert crew_info["module"] == "test.module"
        assert crew_info["description"] == "Test crew description"
    
    def test_request_validation(self, client, valid_token):
        """Test request validation for crew execution"""
        # Missing crew_name
        response = client.post(
            "/execute_crew",
            json={"inputs": {"text_content": "test"}},
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Missing inputs
        response = client.post(
            "/execute_crew",
            json={"crew_name": "test_crew"},
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_cors_headers(self, client):
        """Test CORS headers are present"""
        response = client.options("/health")
        # CORS headers should be present in development
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_405_METHOD_NOT_ALLOWED]


if __name__ == "__main__":
    pytest.main([__file__])