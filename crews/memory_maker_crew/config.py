"""
Memory Maker Crew Configuration Management

This module provides configuration management for the Memory Maker Crew
with environment variable support and validation.
"""

import os
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator
from uuid import UUID


class MemoryMakerConfig(BaseModel):
    """
    Configuration class for Memory Maker Crew with environment variable support.
    
    This class handles all configuration settings for the Memory Maker Crew,
    including service URLs, authentication, timeouts, and retry logic.
    """
    
    # Memory Service Configuration
    memory_service_url: str = Field(
        default="https://memory-external-development.up.railway.app",
        description="URL for the memory service API"
    )
    
    # Authentication Configuration
    api_secret_key: str = Field(
        default="",
        description="Secret key for JWT token generation"
    )
    
    # Timeout and Retry Configuration
    timeout_seconds: int = Field(
        default=30,
        description="Timeout for memory service requests in seconds",
        ge=1,
        le=300
    )
    
    retry_attempts: int = Field(
        default=3,
        description="Number of retry attempts for failed requests",
        ge=1,
        le=10
    )
    
    retry_backoff_factor: float = Field(
        default=2.0,
        description="Exponential backoff factor for retries",
        ge=1.0,
        le=10.0
    )
    
    # Logging Configuration
    enable_debug_logging: bool = Field(
        default=False,
        description="Enable debug logging for development"
    )
    
    # Context-specific settings
    supported_actor_types: List[str] = Field(
        default=["client", "synth", "human", "synth_class", "skill_module"],
        description="List of supported actor types"
    )
    
    default_entity_types: List[str] = Field(
        default=["policy", "procedure", "organization", "concept", "skill"],
        description="Default entity types for memory extraction"
    )
    
    # Text Processing Configuration
    max_text_length: int = Field(
        default=100000,
        description="Maximum allowed text content length",
        ge=1,
        le=1000000
    )
    
    min_text_length: int = Field(
        default=1,
        description="Minimum required text content length",
        ge=1
    )
    
    @field_validator('api_secret_key')
    @classmethod
    def validate_api_secret_key(cls, v):
        """Validate that API secret key is provided."""
        if not v or not v.strip():
            raise ValueError('API_SECRET_KEY environment variable is required')
        return v.strip()
    
    @field_validator('memory_service_url')
    @classmethod
    def validate_memory_service_url(cls, v):
        """Validate memory service URL format."""
        if not v or not v.strip():
            raise ValueError('MEMORY_SERVICE_URL is required')
        
        v = v.strip()
        if not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('MEMORY_SERVICE_URL must start with http:// or https://')
        
        return v
    
    @field_validator('supported_actor_types')
    @classmethod
    def validate_actor_types(cls, v):
        """Validate that actor types list is not empty."""
        if not v:
            raise ValueError('supported_actor_types cannot be empty')
        return v
    
    @field_validator('min_text_length', 'max_text_length')
    @classmethod
    def validate_text_lengths(cls, v, info):
        """Validate text length constraints."""
        if v <= 0:
            raise ValueError(f'{info.field_name} must be greater than 0')
        return v
    
    @model_validator(mode='before')
    @classmethod
    def load_from_environment(cls, values):
        """Load configuration from environment variables."""
        if isinstance(values, dict):
            # Load from environment if not explicitly provided
            if 'api_secret_key' not in values or not values['api_secret_key']:
                values['api_secret_key'] = os.getenv("API_SECRET_KEY", "")
            
            if 'memory_service_url' not in values or not values['memory_service_url']:
                values['memory_service_url'] = os.getenv(
                    "MEMORY_SERVICE_URL", 
                    "https://memory-external-development.up.railway.app"
                )
            
            if 'timeout_seconds' not in values:
                values['timeout_seconds'] = int(os.getenv("MEMORY_MAKER_TIMEOUT", "30"))
            
            if 'retry_attempts' not in values:
                values['retry_attempts'] = int(os.getenv("MEMORY_MAKER_RETRY_ATTEMPTS", "3"))
            
            if 'retry_backoff_factor' not in values:
                values['retry_backoff_factor'] = float(os.getenv("MEMORY_MAKER_RETRY_BACKOFF", "2.0"))
            
            if 'enable_debug_logging' not in values:
                values['enable_debug_logging'] = os.getenv("MEMORY_MAKER_DEBUG", "false").lower() == "true"
            
            if 'max_text_length' not in values:
                values['max_text_length'] = int(os.getenv("MEMORY_MAKER_MAX_TEXT_LENGTH", "100000"))
        
        return values
    
    @model_validator(mode='after')
    def validate_max_greater_than_min(self):
        """Validate that max_text_length is greater than min_text_length."""
        if self.max_text_length <= self.min_text_length:
            raise ValueError('max_text_length must be greater than min_text_length')
        return self
    
    class Config:
        """Pydantic configuration."""
        env_prefix = 'MEMORY_MAKER_'
        case_sensitive = False
        validate_assignment = True
        
    def is_actor_type_supported(self, actor_type: str) -> bool:
        """
        Check if an actor type is supported.
        
        Args:
            actor_type: The actor type to check
            
        Returns:
            True if the actor type is supported, False otherwise
        """
        return actor_type in self.supported_actor_types
    
    def get_retry_delay(self, attempt: int) -> float:
        """
        Calculate retry delay for a given attempt number.
        
        Args:
            attempt: The attempt number (1-based)
            
        Returns:
            Delay in seconds for the retry
        """
        if attempt <= 1:
            return 0.0
        
        # Exponential backoff: base_delay * (backoff_factor ^ (attempt - 1))
        base_delay = 1.0
        delay = base_delay * (self.retry_backoff_factor ** (attempt - 1))
        
        # Cap the maximum delay at 60 seconds
        return min(delay, 60.0)


# Global configuration instance
_config_instance: Optional[MemoryMakerConfig] = None


def get_config() -> MemoryMakerConfig:
    """
    Get the global configuration instance.
    
    Returns:
        MemoryMakerConfig instance
        
    Raises:
        ValueError: If configuration validation fails
    """
    global _config_instance
    
    if _config_instance is None:
        _config_instance = MemoryMakerConfig()
    
    return _config_instance


def reload_config() -> MemoryMakerConfig:
    """
    Reload configuration from environment variables.
    
    Returns:
        New MemoryMakerConfig instance
        
    Raises:
        ValueError: If configuration validation fails
    """
    global _config_instance
    _config_instance = MemoryMakerConfig()
    return _config_instance