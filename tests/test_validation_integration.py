"""
Integration test for book ingestion crew input validation.
Tests the integration between Pydantic validation and crew handler.
"""

import pytest
from uuid import uuid4
from crews.book_ingestion_crew.book_ingestion_crew_handler import BookIngestionCrewHandler


def test_crew_handler_validation_success():
    """Test crew handler with valid input data."""
    handler = BookIngestionCrewHandler()
    
    valid_data = {
        "job_key": "book_ingestion_crew",
        "client_user_id": str(uuid4()),
        "actor_type": "client",
        "actor_id": str(uuid4()),
        "google_drive_folder_path": "https://drive.google.com/drive/folders/1ABC123DEF456",
        "book_title": "Test Manuscript",
        "book_author": "Test Author",
        "book_description": "A test manuscript for validation",
        "language": "en",
        "process_pages_limit": 10
    }
    
    # This should not raise an exception
    result = handler.validate_request(valid_data)
    assert result is True


def test_crew_handler_validation_failure():
    """Test crew handler with invalid input data."""
    handler = BookIngestionCrewHandler()
    
    invalid_data = {
        "job_key": "wrong_job_key",
        "client_user_id": "invalid-uuid",
        "actor_type": "invalid_actor",
        "actor_id": "invalid-uuid-2",
        "google_drive_folder_path": "",
        "book_title": "",
        "book_author": "",
        "language": "invalid_lang"
    }
    
    # This should raise a ValueError with detailed error message
    with pytest.raises(ValueError) as exc_info:
        handler.validate_request(invalid_data)
    
    error_message = str(exc_info.value)
    assert "Input validation failed" in error_message
    assert "job_key" in error_message
    assert "client_user_id" in error_message
    assert "actor_type" in error_message


def test_crew_handler_missing_required_fields():
    """Test crew handler with missing required fields."""
    handler = BookIngestionCrewHandler()
    
    incomplete_data = {
        "job_key": "book_ingestion_crew",
        "client_user_id": str(uuid4()),
        # Missing other required fields
    }
    
    with pytest.raises(ValueError) as exc_info:
        handler.validate_request(incomplete_data)
    
    error_message = str(exc_info.value)
    assert "Input validation failed" in error_message


def test_crew_handler_language_validation():
    """Test crew handler language validation specifically."""
    handler = BookIngestionCrewHandler()
    
    # Test with invalid language
    data_invalid_lang = {
        "job_key": "book_ingestion_crew",
        "client_user_id": str(uuid4()),
        "actor_type": "client",
        "actor_id": str(uuid4()),
        "google_drive_folder_path": "https://drive.google.com/drive/folders/1ABC123",
        "book_title": "Test Book",
        "book_author": "Test Author",
        "language": "invalid_language"
    }
    
    with pytest.raises(ValueError) as exc_info:
        handler.validate_request(data_invalid_lang)
    
    assert "language" in str(exc_info.value)
    
    # Test with valid languages
    valid_languages = ["en", "es", "fr", "de", "it", "pt", "nl", "pl", "ru", "ja", "zh"]
    
    for lang in valid_languages:
        data_valid_lang = data_invalid_lang.copy()
        data_valid_lang["language"] = lang
        
        # Should not raise exception
        result = handler.validate_request(data_valid_lang)
        assert result is True


def test_crew_handler_process_pages_limit():
    """Test crew handler process_pages_limit validation."""
    handler = BookIngestionCrewHandler()
    
    base_data = {
        "job_key": "book_ingestion_crew",
        "client_user_id": str(uuid4()),
        "actor_type": "client",
        "actor_id": str(uuid4()),
        "google_drive_folder_path": "https://drive.google.com/drive/folders/1ABC123",
        "book_title": "Test Book",
        "book_author": "Test Author",
        "language": "en"
    }
    
    # Test with valid limits
    valid_limits = [0, 1, 10, 100]
    for limit in valid_limits:
        test_data = base_data.copy()
        test_data["process_pages_limit"] = limit
        result = handler.validate_request(test_data)
        assert result is True
    
    # Test with invalid limit
    test_data = base_data.copy()
    test_data["process_pages_limit"] = -1
    
    with pytest.raises(ValueError) as exc_info:
        handler.validate_request(test_data)
    
    assert "process_pages_limit" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__])