#!/usr/bin/env python3
"""
Direct test of MemoryMakerConfig without package imports.
"""

import os
import sys
from unittest.mock import patch

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import directly from the config module
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'crews', 'memory_maker_crew'))

from config import MemoryMakerConfig, get_config, reload_config


def test_basic_config():
    """Test basic configuration functionality."""
    print("Testing basic configuration...")
    
    with patch.dict(os.environ, {
        'API_SECRET_KEY': 'test-secret-key',
        'MEMORY_SERVICE_URL': 'https://test-memory-service.com'
    }, clear=False):
        config = MemoryMakerConfig()
        
        assert config.api_secret_key == 'test-secret-key'
        assert config.memory_service_url == 'https://test-memory-service.com'
        assert config.timeout_seconds == 30
        assert config.retry_attempts == 3
        assert config.retry_backoff_factor == 2.0
        assert config.enable_debug_logging is False
        assert 'client' in config.supported_actor_types
        assert 'synth_class' in config.supported_actor_types
        assert 'skill_module' in config.supported_actor_types
        
        print("✓ Basic configuration test passed")


def test_environment_override():
    """Test environment variable override."""
    print("Testing environment variable override...")
    
    env_vars = {
        'API_SECRET_KEY': 'custom-secret',
        'MEMORY_SERVICE_URL': 'https://custom-memory-service.com',
        'MEMORY_MAKER_TIMEOUT': '60',
        'MEMORY_MAKER_RETRY_ATTEMPTS': '5',
        'MEMORY_MAKER_RETRY_BACKOFF': '3.0',
        'MEMORY_MAKER_DEBUG': 'true',
        'MEMORY_MAKER_MAX_TEXT_LENGTH': '200000'
    }
    
    with patch.dict(os.environ, env_vars, clear=False):
        config = MemoryMakerConfig()
        
        assert config.api_secret_key == 'custom-secret'
        assert config.memory_service_url == 'https://custom-memory-service.com'
        assert config.timeout_seconds == 60
        assert config.retry_attempts == 5
        assert config.retry_backoff_factor == 3.0
        assert config.enable_debug_logging is True
        assert config.max_text_length == 200000
        
        print("✓ Environment override test passed")


def test_validation_errors():
    """Test validation error handling."""
    print("Testing validation errors...")
    
    # Test empty API key with direct instantiation
    try:
        MemoryMakerConfig(
            api_secret_key="",
            memory_service_url="https://test.com"
        )
        assert False, "Should have raised validation error"
    except Exception as e:
        assert 'API_SECRET_KEY environment variable is required' in str(e)
        print("✓ Empty API key validation test passed")
    
    # Test invalid URL with direct instantiation
    try:
        MemoryMakerConfig(
            api_secret_key="test-key",
            memory_service_url="invalid-url"
        )
        assert False, "Should have raised validation error"
    except Exception as e:
        assert 'must start with http:// or https://' in str(e)
        print("✓ Invalid URL validation test passed")
    
    # Test environment variable validation
    try:
        with patch.dict(os.environ, {'API_SECRET_KEY': '', 'MEMORY_SERVICE_URL': 'https://test.com'}, clear=True):
            MemoryMakerConfig()
        assert False, "Should have raised validation error"
    except Exception as e:
        assert 'API_SECRET_KEY environment variable is required' in str(e)
        print("✓ Environment variable validation test passed")


if __name__ == '__main__':
    print("Running MemoryMakerConfig tests...")
    print("=" * 50)
    
    try:
        test_basic_config()
        test_environment_override()
        test_validation_errors()
        
        print("=" * 50)
        print("✅ All configuration tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)