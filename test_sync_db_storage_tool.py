#!/usr/bin/env python3
"""Test script for SyncDBStorageTool."""
import json
import os
import sys
import uuid
from datetime import datetime

# Add the tools directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))

from sync_db_storage_tool import SyncDBStorageTool


def test_page_number_extraction():
    """Test page number extraction from various filename patterns."""
    print("Testing page number extraction...")
    
    tool = SyncDBStorageTool()
    
    test_cases = [
        ("page_001.jpg", 1),
        ("page 5.png", 5),
        ("page15.tiff", 15),
        ("p_10.jpg", 10),
        ("p 25.png", 25),
        ("p99.webp", 99),
        ("pg_007.jpg", 7),
        ("pg 12.png", 12),
        ("pg33.gif", 33),
        ("manuscript_001.jpg", 1),
        ("scan_042.png", 42),
        ("book_page_123.tiff", 123),
        ("001_handwritten.jpg", 1),
        ("025_manuscript.png", 25),
        ("document_15_final.jpg", 15),
        ("handwriting_099.png", 99),
        ("IMG_20240101_001.jpg", 1),
        ("scan001.jpg", 1),
        ("page.jpg", None),  # Should fail
        ("document.png", None),  # Should fail
        ("", None),  # Should fail
    ]
    
    passed = 0
    failed = 0
    
    for filename, expected in test_cases:
        result = tool._extract_page_number_from_filename(filename)
        if result == expected:
            print(f"✓ {filename} -> {result}")
            passed += 1
        else:
            print(f"✗ {filename} -> {result} (expected {expected})")
            failed += 1
    
    print(f"\nPage number extraction tests: {passed} passed, {failed} failed")
    return failed == 0


def test_input_validation():
    """Test input validation with various parameter combinations."""
    print("\nTesting input validation...")
    
    tool = SyncDBStorageTool()
    
    # Test valid input
    valid_params = {
        "client_user_id": str(uuid.uuid4()),
        "book_key": "test_book_001",
        "page_number": 1,
        "file_name": "page_001.jpg",
        "language_code": "en",
        "page_text": "This is a test page with some transcribed text.",
        "ocr_metadata": {
            "file_id": "test_file_123",
            "processing_stats": {
                "total_words": 10,
                "normal_transcription": 8,
                "context_logic_transcription": 2,
                "unable_to_transcribe": 0
            },
            "unclear_sections": [],
            "ocr_passes": 3,
            "model_used": "gpt-4o"
        }
    }
    
    try:
        from sync_db_storage_tool import SyncDBStorageToolSchema
        schema = SyncDBStorageToolSchema(**valid_params)
        print("✓ Valid input validation passed")
    except Exception as e:
        print(f"✗ Valid input validation failed: {e}")
        return False
    
    # Test missing required fields
    invalid_params = valid_params.copy()
    del invalid_params["client_user_id"]
    
    try:
        schema = SyncDBStorageToolSchema(**invalid_params)
        print("✗ Missing required field validation should have failed")
        return False
    except Exception:
        print("✓ Missing required field validation passed")
    
    # Test page number extraction when not provided
    no_page_num_params = valid_params.copy()
    del no_page_num_params["page_number"]
    
    try:
        schema = SyncDBStorageToolSchema(**no_page_num_params)
        print("✓ Optional page number validation passed")
    except Exception as e:
        print(f"✗ Optional page number validation failed: {e}")
        return False
    
    print("Input validation tests passed")
    return True


def test_tool_interface():
    """Test the tool interface without actual database operations."""
    print("\nTesting tool interface...")
    
    tool = SyncDBStorageTool()
    
    # Check tool properties
    assert tool.name == "sync_db_storage"
    assert "Store book page to database" in tool.description
    assert tool.args_schema is not None
    print("✓ Tool properties are correct")
    
    # Test with mock parameters (will fail due to no database, but should validate input)
    test_params = {
        "client_user_id": str(uuid.uuid4()),
        "book_key": "test_book_001",
        "file_name": "page_001.jpg",
        "language_code": "en",
        "page_text": "Test transcription text.",
        "ocr_metadata": {"test": "data"}
    }
    
    # This will fail due to no database connection, but should validate the interface
    result_str = tool._run(**test_params)
    result = json.loads(result_str)
    
    # Should return error due to no database, but structure should be correct
    assert "success" in result
    assert result["success"] is False
    assert "error" in result
    print("✓ Tool interface works correctly")
    
    print("Tool interface tests passed")
    return True


def test_error_handling():
    """Test error handling scenarios."""
    print("\nTesting error handling...")
    
    tool = SyncDBStorageTool()
    
    # Test with invalid parameters
    try:
        result_str = tool._run()  # No parameters
        result = json.loads(result_str)
        assert result["success"] is False
        assert "error" in result
        print("✓ Empty parameters error handling works")
    except Exception as e:
        print(f"✗ Empty parameters error handling failed: {e}")
        return False
    
    # Test with invalid client_user_id format
    try:
        result_str = tool._run(
            client_user_id="invalid-uuid",
            book_key="test",
            file_name="test.jpg",
            language_code="en",
            page_text="test"
        )
        result = json.loads(result_str)
        # Should handle gracefully
        assert "success" in result
        print("✓ Invalid UUID error handling works")
    except Exception as e:
        print(f"✗ Invalid UUID error handling failed: {e}")
        return False
    
    print("Error handling tests passed")
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("SyncDBStorageTool Test Suite")
    print("=" * 60)
    
    tests = [
        test_page_number_extraction,
        test_input_validation,
        test_tool_interface,
        test_error_handling,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())