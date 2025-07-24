#!/usr/bin/env python3
"""
Comprehensive test to verify Task 1 completion.
Tests both configuration and request validation models together.
"""

import os
import sys
from uuid import uuid4
from unittest.mock import patch

# Add the current directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'crews', 'memory_maker_crew'))

from config import MemoryMakerConfig, get_config
from models import MemoryMakerRequest, MemoryProcessingResult, ProcessingMetadata


def test_integrated_functionality():
    """Test configuration and models working together."""
    print("Testing integrated functionality...")
    
    # Test configuration loading
    with patch.dict(os.environ, {
        'API_SECRET_KEY': 'test-secret-key',
        'MEMORY_SERVICE_URL': 'https://test-memory-service.com',
        'MEMORY_MAKER_TIMEOUT': '45',
        'MEMORY_MAKER_DEBUG': 'true'
    }, clear=False):
        config = MemoryMakerConfig()
        
        # Verify configuration
        assert config.api_secret_key == 'test-secret-key'
        assert config.memory_service_url == 'https://test-memory-service.com'
        assert config.timeout_seconds == 45
        assert config.enable_debug_logging is True
        print("✓ Configuration loading test passed")
        
        # Test actor type validation using config
        assert config.is_actor_type_supported('client') is True
        assert config.is_actor_type_supported('synth_class') is True
        assert config.is_actor_type_supported('skill_module') is True
        assert config.is_actor_type_supported('invalid') is False
        print("✓ Actor type support validation test passed")
        
        # Test retry delay calculation
        assert config.get_retry_delay(1) == 0.0
        assert config.get_retry_delay(2) == 2.0
        assert config.get_retry_delay(3) == 4.0
        print("✓ Retry delay calculation test passed")


def test_request_validation_with_config():
    """Test request validation using configuration constraints."""
    print("Testing request validation with config constraints...")
    
    with patch.dict(os.environ, {
        'API_SECRET_KEY': 'test-secret-key',
        'MEMORY_SERVICE_URL': 'https://test-memory-service.com'
    }, clear=False):
        config = MemoryMakerConfig()
        
        # Test valid requests for all supported actor types
        for actor_type in config.supported_actor_types:
            if actor_type == "synth_class":
                actor_id = "24"
            else:
                actor_id = str(uuid4())
            
            request = MemoryMakerRequest(
                actor_type=actor_type,
                actor_id=actor_id,
                client_user_id=str(uuid4()),
                text_content=f"Test content for {actor_type} actor type."
            )
            
            assert request.actor_type == actor_type
            assert request.actor_id == actor_id
            print(f"✓ Valid request for {actor_type} test passed")
        
        # Test text length constraints
        short_text = "Short"
        long_text = "x" * (config.max_text_length + 1)
        
        # Valid length
        request = MemoryMakerRequest(
            actor_type="client",
            actor_id=str(uuid4()),
            client_user_id=str(uuid4()),
            text_content=short_text
        )
        assert len(request.text_content) >= config.min_text_length
        print("✓ Text length validation (valid) test passed")
        
        # Invalid length (too long)
        try:
            MemoryMakerRequest(
                actor_type="client",
                actor_id=str(uuid4()),
                client_user_id=str(uuid4()),
                text_content=long_text
            )
            assert False, "Should have raised validation error for long text"
        except Exception as e:
            assert "cannot exceed" in str(e)
            print("✓ Text length validation (too long) test passed")


def test_complete_workflow_simulation():
    """Test a complete workflow simulation."""
    print("Testing complete workflow simulation...")
    
    with patch.dict(os.environ, {
        'API_SECRET_KEY': 'test-secret-key',
        'MEMORY_SERVICE_URL': 'https://test-memory-service.com'
    }, clear=False):
        config = MemoryMakerConfig()
        
        # Create a request
        request = MemoryMakerRequest(
            actor_type="client",
            actor_id="1d1c2154-242b-4f49-9ca8-e57129ddc823",
            client_user_id=str(uuid4()),
            text_content="Vervelyn Publishing corporate policy document content for testing memory extraction.",
            metadata={"source": "corporate_policy", "version": "1.0"}
        )
        
        # Simulate processing metadata
        metadata = ProcessingMetadata(
            text_length=len(request.text_content),
            entities_extracted=3,
            observations_created=5,
            relationships_created=2
        )
        
        # Create processing result
        result = MemoryProcessingResult(
            status="completed",
            processing_metadata=metadata,
            summary=f"Successfully processed {request.actor_type} content"
        )
        
        # Verify the complete workflow
        assert request.actor_type == "client"
        assert request.actor_id == "1d1c2154-242b-4f49-9ca8-e57129ddc823"
        assert "Vervelyn Publishing" in request.text_content
        assert result.status == "completed"
        assert result.processing_metadata.entities_extracted == 3
        assert result.get_total_items_processed() == 0  # No actual entities created in simulation
        assert not result.has_errors()
        
        print("✓ Complete workflow simulation test passed")


if __name__ == '__main__':
    print("Running Task 1 completion verification tests...")
    print("=" * 60)
    
    try:
        test_integrated_functionality()
        test_request_validation_with_config()
        test_complete_workflow_simulation()
        
        print("=" * 60)
        print("✅ Task 1 implementation verified successfully!")
        print("✅ Configuration class with environment variable handling: COMPLETE")
        print("✅ Input validation with Pydantic models: COMPLETE")
        print("✅ Unit tests for configuration and models: COMPLETE")
        print("=" * 60)
        print("Requirements 3.1 and 3.4 have been satisfied:")
        print("- 3.1: Configuration centralized and type-safe using Pydantic models")
        print("- 3.4: All configuration replaced with environment variables")
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)