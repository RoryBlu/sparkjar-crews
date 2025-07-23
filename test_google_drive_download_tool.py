#!/usr/bin/env python3
"""Test script for GoogleDriveDownloadTool.

This script tests the enhanced GoogleDriveDownloadTool implementation
to ensure it meets all requirements for the book ingestion crew.
"""
import json
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add the tools directory to the path
sys.path.insert(0, str(Path(__file__).parent / "tools"))

from google_drive_download_tool import GoogleDriveDownloadTool, GoogleDriveDownloadInput, SUPPORTED_IMAGE_FORMATS

def test_input_validation():
    """Test input validation for the tool."""
    print("Testing input validation...")
    
    # Test valid inputs
    valid_inputs = [
        {"file_id": "test123", "file_name": "page1.png", "client_user_id": "550e8400-e29b-41d4-a716-446655440000"},
        {"file_id": "test456", "file_name": "manuscript.jpg", "client_user_id": "550e8400-e29b-41d4-a716-446655440001"},
        {"file_id": "test789", "file_name": "scan.tiff", "client_user_id": "550e8400-e29b-41d4-a716-446655440002"},
    ]
    
    for input_data in valid_inputs:
        try:
            validated = GoogleDriveDownloadInput(**input_data)
            print(f"✓ Valid input: {input_data['file_name']}")
        except Exception as e:
            print(f"✗ Unexpected validation error for {input_data}: {e}")
            return False
    
    # Test invalid inputs
    invalid_inputs = [
        {"file_id": "", "file_name": "page1.png", "client_user_id": "550e8400-e29b-41d4-a716-446655440000"},  # Empty file_id
        {"file_id": "test123", "file_name": "", "client_user_id": "550e8400-e29b-41d4-a716-446655440000"},  # Empty file_name
        {"file_id": "test123", "file_name": "page1.png", "client_user_id": ""},  # Empty client_user_id
        {"file_id": "test123", "file_name": "document.pdf", "client_user_id": "550e8400-e29b-41d4-a716-446655440000"},  # Unsupported format
        {"file_id": "test123", "file_name": "noextension", "client_user_id": "550e8400-e29b-41d4-a716-446655440000"},  # No extension
    ]
    
    for input_data in invalid_inputs:
        try:
            validated = GoogleDriveDownloadInput(**input_data)
            print(f"✗ Should have failed validation: {input_data}")
            return False
        except Exception as e:
            print(f"✓ Correctly rejected invalid input: {input_data.get('file_name', 'invalid')} - {e}")
    
    return True

def test_supported_formats():
    """Test that all required image formats are supported."""
    print("\nTesting supported image formats...")
    
    required_formats = ['png', 'jpg', 'jpeg', 'webp', 'gif', 'bmp', 'tiff']
    
    for format_ext in required_formats:
        if format_ext not in SUPPORTED_IMAGE_FORMATS:
            print(f"✗ Missing required format: {format_ext}")
            return False
        print(f"✓ Supported format: {format_ext} -> {SUPPORTED_IMAGE_FORMATS[format_ext]}")
    
    # Test case variations
    test_files = [
        "page1.PNG",  # Uppercase
        "page2.Jpg",  # Mixed case
        "page3.TIFF", # Uppercase
    ]
    
    for file_name in test_files:
        try:
            input_data = {"file_id": "test123", "file_name": file_name, "client_user_id": "550e8400-e29b-41d4-a716-446655440000"}
            validated = GoogleDriveDownloadInput(**input_data)
            print(f"✓ Case insensitive validation: {file_name}")
        except Exception as e:
            print(f"✗ Case sensitivity issue with {file_name}: {e}")
            return False
    
    return True

def test_tool_initialization():
    """Test tool initialization and basic properties."""
    print("\nTesting tool initialization...")
    
    tool = GoogleDriveDownloadTool()
    
    # Check basic properties
    if tool.name != "google_drive_download":
        print(f"✗ Wrong tool name: {tool.name}")
        return False
    
    if not tool.description:
        print("✗ Missing tool description")
        return False
    
    if tool.args_schema != GoogleDriveDownloadInput:
        print("✗ Wrong args schema")
        return False
    
    # Check temp directories tracking
    if not hasattr(tool, '_temp_dirs'):
        print("✗ Missing temp directories tracking")
        return False
    
    print("✓ Tool initialization successful")
    return True

@patch('tools.google_drive_tool.service_account')
@patch('tools.google_drive_tool.build')
@patch('tools.google_drive_tool.create_engine')
@patch('tools.google_drive_tool.sessionmaker')
@patch('tools.google_drive_download_tool.GoogleDriveTool')
def test_successful_download(mock_drive_tool_class, mock_sessionmaker, mock_create_engine, mock_build, mock_service_account):
    """Test successful file download scenario."""
    print("\nTesting successful download...")
    
    # Mock database session and queries
    mock_session = Mock()
    mock_sessionmaker.return_value.return_value.__enter__.return_value = mock_session
    
    # Mock client lookup
    mock_user_result = Mock()
    mock_user_result.scalar_one_or_none.return_value = "client-uuid-123"
    
    # Mock proper service account credentials
    service_account_data = {
        'type': 'service_account',
        'project_id': 'test-project',
        'private_key_id': 'test-key-id',
        'private_key': '-----BEGIN PRIVATE KEY-----\ntest-key\n-----END PRIVATE KEY-----\n',
        'client_email': 'test@test-project.iam.gserviceaccount.com',
        'client_id': 'test-client-id',
        'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
        'token_uri': 'https://oauth2.googleapis.com/token',
        'auth_provider_x509_cert_url': 'https://www.googleapis.com/oauth2/v1/certs',
        'client_x509_cert_url': 'https://www.googleapis.com/robot/v1/metadata/x509/test%40test-project.iam.gserviceaccount.com'
    }
    
    mock_session.execute.side_effect = [
        mock_user_result,  # First call for user lookup
        Mock(scalar_one_or_none=lambda: Mock(secrets_metadata=service_account_data))  # Second call for credentials
    ]
    
    # Mock Google API components
    mock_credentials = Mock()
    mock_service_account.Credentials.from_service_account_info.return_value = mock_credentials
    mock_service = Mock()
    mock_build.return_value = mock_service
    
    # Mock the GoogleDriveTool
    mock_drive_tool = Mock()
    mock_drive_tool_class.return_value = mock_drive_tool
    
    # Mock the service
    mock_service = Mock()
    mock_drive_tool._get_service.return_value = mock_service
    
    # Mock file metadata
    mock_service.files().get().execute.return_value = {
        'id': 'test123',
        'name': 'page1.png',
        'mimeType': 'image/png',
        'size': '12345'
    }
    
    # Mock successful download
    mock_download_path = "/tmp/test/page1.png"
    mock_drive_tool._download_file.return_value = mock_download_path
    
    # Mock file existence and size
    with patch('pathlib.Path.exists', return_value=True), \
         patch('pathlib.Path.stat') as mock_stat:
        
        mock_stat.return_value.st_size = 12345
        
        tool = GoogleDriveDownloadTool()
        # Use a proper UUID format for client_user_id
        result = tool._run("test123", "page1.png", "550e8400-e29b-41d4-a716-446655440000")
        
        # Parse result
        result_data = json.loads(result)
        
        if not result_data.get('success'):
            print(f"✗ Download failed: {result_data}")
            return False
        
        if result_data.get('local_path') != mock_download_path:
            print(f"✗ Wrong local path: {result_data.get('local_path')}")
            return False
        
        if result_data.get('file_size') != 12345:
            print(f"✗ Wrong file size: {result_data.get('file_size')}")
            return False
        
        print("✓ Successful download test passed")
        return True

@patch('tools.google_drive_tool.service_account')
@patch('tools.google_drive_tool.build')
@patch('tools.google_drive_tool.create_engine')
@patch('tools.google_drive_tool.sessionmaker')
@patch('tools.google_drive_download_tool.GoogleDriveTool')
def test_error_handling(mock_drive_tool_class, mock_sessionmaker, mock_create_engine, mock_build, mock_service_account):
    """Test error handling scenarios."""
    print("\nTesting error handling...")
    
    # Mock database session for file not found test
    mock_session = Mock()
    mock_sessionmaker.return_value.return_value.__enter__.return_value = mock_session
    
    # Mock client lookup
    mock_user_result = Mock()
    mock_user_result.scalar_one_or_none.return_value = "client-uuid-123"
    
    # Mock proper service account credentials
    service_account_data = {
        'type': 'service_account',
        'project_id': 'test-project',
        'private_key_id': 'test-key-id',
        'private_key': '-----BEGIN PRIVATE KEY-----\ntest-key\n-----END PRIVATE KEY-----\n',
        'client_email': 'test@test-project.iam.gserviceaccount.com',
        'client_id': 'test-client-id',
        'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
        'token_uri': 'https://oauth2.googleapis.com/token',
        'auth_provider_x509_cert_url': 'https://www.googleapis.com/oauth2/v1/certs',
        'client_x509_cert_url': 'https://www.googleapis.com/robot/v1/metadata/x509/test%40test-project.iam.gserviceaccount.com'
    }
    
    mock_session.execute.side_effect = [
        mock_user_result,  # First call for user lookup
        Mock(scalar_one_or_none=lambda: Mock(secrets_metadata=service_account_data))  # Second call for credentials
    ]
    
    # Mock Google API components
    mock_credentials = Mock()
    mock_service_account.Credentials.from_service_account_info.return_value = mock_credentials
    mock_service = Mock()
    mock_build.return_value = mock_service
    
    # Test file not found
    mock_drive_tool = Mock()
    mock_drive_tool_class.return_value = mock_drive_tool
    
    mock_service = Mock()
    mock_drive_tool._get_service.return_value = mock_service
    
    # Mock file not found
    mock_service.files().get().execute.side_effect = Exception("File not found")
    
    tool = GoogleDriveDownloadTool()
    # Use proper UUID format
    result = tool._run("nonexistent", "page1.png", "550e8400-e29b-41d4-a716-446655440000")
    
    result_data = json.loads(result)
    if result_data.get('success'):
        print("✗ Should have failed for non-existent file")
        return False
    
    if result_data.get('error_type') != 'download_error':
        print(f"✗ Wrong error type: {result_data.get('error_type')}")
        return False
    
    print("✓ File not found error handling passed")
    
    # Test invalid format - this should fail at validation level before hitting database
    result = tool._run("test123", "document.pdf", "550e8400-e29b-41d4-a716-446655440000")
    result_data = json.loads(result)
    
    if result_data.get('success'):
        print("✗ Should have failed for invalid format")
        return False
    
    if result_data.get('error_type') != 'validation_error':
        print(f"✗ Wrong error type for validation: {result_data.get('error_type')}")
        return False
    
    print("✓ Invalid format error handling passed")
    return True

def main():
    """Run all tests."""
    print("Testing GoogleDriveDownloadTool Implementation")
    print("=" * 50)
    
    tests = [
        test_input_validation,
        test_supported_formats,
        test_tool_initialization,
        test_successful_download,
        test_error_handling,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print(f"✗ Test failed: {test.__name__}")
        except Exception as e:
            print(f"✗ Test error in {test.__name__}: {e}")
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("✓ All tests passed! GoogleDriveDownloadTool is ready for production.")
        return True
    else:
        print("✗ Some tests failed. Please review the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)