#!/usr/bin/env python3
"""
Debug config validation.
"""

import os
import sys
from unittest.mock import patch

# Add the current directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'crews', 'memory_maker_crew'))

from config import MemoryMakerConfig


def debug_validation():
    """Debug validation behavior."""
    print("Current environment variables:")
    for key in ['API_SECRET_KEY', 'MEMORY_SERVICE_URL']:
        print(f"  {key}: {os.environ.get(key, 'NOT SET')}")
    
    print("\nTesting with empty API key...")
    try:
        with patch.dict(os.environ, {'API_SECRET_KEY': '', 'MEMORY_SERVICE_URL': 'https://test.com'}, clear=True):
            print("Environment during test:")
            print(f"  API_SECRET_KEY: '{os.environ.get('API_SECRET_KEY', 'NOT SET')}'")
            print(f"  MEMORY_SERVICE_URL: '{os.environ.get('MEMORY_SERVICE_URL', 'NOT SET')}'")
            
            config = MemoryMakerConfig()
            print(f"Config created successfully with api_secret_key: '{config.api_secret_key}'")
            
    except Exception as e:
        print(f"Validation error (expected): {e}")
        print(f"Error type: {type(e)}")


if __name__ == '__main__':
    debug_validation()