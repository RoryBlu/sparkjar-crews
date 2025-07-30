"""
Unit tests for Memory Maker Crew Configuration.
"""

import os
import pytest
from unittest.mock import patch
from pydantic import ValidationError

from ..config import MemoryMakerConfig, get_config, reload_config


class TestMemoryMakerConfig:
    """Test cases for MemoryMakerConfig class."""
    
    def test_default_configuration(self):
        """Test configuration with default values."""
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
            assert config.max_text_length == 100000
            assert config.min_text_length == 1
    
    def test_environment_variable_override(self):
        """Test configuration loading from environment variables."""
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
    
    def test_missing_api_secret_key(self):
        """Test validation error when API secret key is missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                MemoryMakerConfig()
            
            assert 'API_SECRET_KEY environment variable is required' in str(exc_info.value)
    
    def test_empty_api_secret_key(self):
        """Test validation error when API secret key is empty."""
        with patch.dict(os.environ, {'API_SECRET_KEY': '   '}, clear=False):
            with pytest.raises(ValidationError) as exc_info:
                MemoryMakerConfig()
            
            assert 'API_SECRET_KEY environment variable is required' in str(exc_info.value)
    
    def test_invalid_memory_service_url(self):
        """Test validation error for invalid memory service URL."""
        with patch.dict(os.environ, {
            'API_SECRET_KEY': 'test-key',
            'MEMORY_SERVICE_URL': 'invalid-url'
        }, clear=False):
            with pytest.raises(ValidationError) as exc_info:
                MemoryMakerConfig()
            
            assert 'must start with http:// or https://' in str(exc_info.value)
    
    def test_empty_memory_service_url(self):
        """Test validation error for empty memory service URL."""
        with patch.dict(os.environ, {
            'API_SECRET_KEY': 'test-key',
            'MEMORY_SERVICE_URL': ''
        }, clear=False):
            with pytest.raises(ValidationError) as exc_info:
                MemoryMakerConfig()
            
            assert 'MEMORY_SERVICE_URL is required' in str(exc_info.value)
    
    def test_invalid_timeout_range(self):
        """Test validation error for timeout out of range."""
        with patch.dict(os.environ, {
            'API_SECRET_KEY': 'test-key',
            'MEMORY_SERVICE_URL': 'https://test.com',
            'MEMORY_MAKER_TIMEOUT': '0'
        }, clear=False):
            with pytest.raises(ValidationError) as exc_info:
                MemoryMakerConfig()
            
            assert 'greater than or equal to 1' in str(exc_info.value)
    
    def test_invalid_retry_attempts_range(self):
        """Test validation error for retry attempts out of range."""
        with patch.dict(os.environ, {
            'API_SECRET_KEY': 'test-key',
            'MEMORY_SERVICE_URL': 'https://test.com',
            'MEMORY_MAKER_RETRY_ATTEMPTS': '0'
        }, clear=False):
            with pytest.raises(ValidationError) as exc_info:
                MemoryMakerConfig()
            
            assert 'greater than or equal to 1' in str(exc_info.value)
    
    def test_invalid_backoff_factor_range(self):
        """Test validation error for backoff factor out of range."""
        with patch.dict(os.environ, {
            'API_SECRET_KEY': 'test-key',
            'MEMORY_SERVICE_URL': 'https://test.com',
            'MEMORY_MAKER_RETRY_BACKOFF': '0.5'
        }, clear=False):
            with pytest.raises(ValidationError) as exc_info:
                MemoryMakerConfig()
            
            assert 'greater than or equal to 1' in str(exc_info.value)
    
    def test_max_text_length_less_than_min(self):
        """Test validation error when max_text_length is less than min_text_length."""
        with patch.dict(os.environ, {
            'API_SECRET_KEY': 'test-key',
            'MEMORY_SERVICE_URL': 'https://test.com'
        }, clear=False):
            with pytest.raises(ValidationError):
                MemoryMakerConfig(min_text_length=100, max_text_length=50)
    
    def test_is_actor_type_supported(self):
        """Test actor type support checking."""
        with patch.dict(os.environ, {
            'API_SECRET_KEY': 'test-key',
            'MEMORY_SERVICE_URL': 'https://test.com'
        }, clear=False):
            config = MemoryMakerConfig()
            
            assert config.is_actor_type_supported('client') is True
            assert config.is_actor_type_supported('synth_class') is True
            assert config.is_actor_type_supported('skill_module') is True
            assert config.is_actor_type_supported('invalid_type') is False
    
    def test_get_retry_delay(self):
        """Test retry delay calculation."""
        with patch.dict(os.environ, {
            'API_SECRET_KEY': 'test-key',
            'MEMORY_SERVICE_URL': 'https://test.com',
            'MEMORY_MAKER_RETRY_BACKOFF': '2.0'
        }, clear=False):
            config = MemoryMakerConfig()
            
            # First attempt should have no delay
            assert config.get_retry_delay(1) == 0.0
            
            # Second attempt: 1.0 * (2.0 ^ 1) = 2.0
            assert config.get_retry_delay(2) == 2.0
            
            # Third attempt: 1.0 * (2.0 ^ 2) = 4.0
            assert config.get_retry_delay(3) == 4.0
            
            # Fourth attempt: 1.0 * (2.0 ^ 3) = 8.0
            assert config.get_retry_delay(4) == 8.0
    
    def test_get_retry_delay_max_cap(self):
        """Test retry delay maximum cap."""
        with patch.dict(os.environ, {
            'API_SECRET_KEY': 'test-key',
            'MEMORY_SERVICE_URL': 'https://test.com',
            'MEMORY_MAKER_RETRY_BACKOFF': '10.0'
        }, clear=False):
            config = MemoryMakerConfig()
            
            # High attempt number should be capped at 60 seconds
            delay = config.get_retry_delay(10)
            assert delay == 60.0


class TestConfigurationSingleton:
    """Test cases for configuration singleton functions."""
    
    def test_get_config_singleton(self):
        """Test that get_config returns the same instance."""
        with patch.dict(os.environ, {
            'API_SECRET_KEY': 'test-key',
            'MEMORY_SERVICE_URL': 'https://test.com'
        }, clear=False):
            config1 = get_config()
            config2 = get_config()
            
            assert config1 is config2
    
    def test_reload_config(self):
        """Test configuration reloading."""
        with patch.dict(os.environ, {
            'API_SECRET_KEY': 'test-key',
            'MEMORY_SERVICE_URL': 'https://test.com',
            'MEMORY_MAKER_TIMEOUT': '30'
        }, clear=False):
            config1 = get_config()
            assert config1.timeout_seconds == 30
        
        # Change environment variable
        with patch.dict(os.environ, {
            'API_SECRET_KEY': 'test-key',
            'MEMORY_SERVICE_URL': 'https://test.com',
            'MEMORY_MAKER_TIMEOUT': '60'
        }, clear=False):
            config2 = reload_config()
            assert config2.timeout_seconds == 60
            
            # Verify it's a new instance
            assert config1 is not config2
    
    def test_config_validation_error_propagation(self):
        """Test that validation errors are properly propagated."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValidationError):
                reload_config()