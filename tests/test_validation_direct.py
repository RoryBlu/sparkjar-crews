#!/usr/bin/env python3
"""
Test validation directly.
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'crews', 'memory_maker_crew'))

from config import MemoryMakerConfig


def test_direct_validation():
    """Test validation with direct values."""
    print("Testing direct validation...")
    
    # Test with empty API key
    try:
        config = MemoryMakerConfig(
            api_secret_key="",
            memory_service_url="https://test.com"
        )
        print(f"Config created with empty key: '{config.api_secret_key}'")
    except Exception as e:
        print(f"Validation error (expected): {e}")
    
    # Test with invalid URL
    try:
        config = MemoryMakerConfig(
            api_secret_key="test-key",
            memory_service_url="invalid-url"
        )
        print(f"Config created with invalid URL: '{config.memory_service_url}'")
    except Exception as e:
        print(f"Validation error (expected): {e}")
    
    # Test with valid values
    try:
        config = MemoryMakerConfig(
            api_secret_key="test-key",
            memory_service_url="https://test.com"
        )
        print(f"Config created successfully: key='{config.api_secret_key}', url='{config.memory_service_url}'")
    except Exception as e:
        print(f"Unexpected error: {e}")


if __name__ == '__main__':
    test_direct_validation()