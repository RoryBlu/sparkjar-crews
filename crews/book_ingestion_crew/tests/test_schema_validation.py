"""
Comprehensive unit tests for input validation schema.

This module implements task 10 requirements:
- Test input validation schema with various scenarios
- Test validation error messages
- Test edge cases and optional parameters
- Validate all required fields

Requirements: 4.1, 4.2, 4.3, 4.4
"""
import pytest
from pathlib import Path
import sys

# Import schema validation
sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from crews.book_ingestion_crew.schema import (
    validate_book_ingestion_input,
    BookIngestionContext,
    ValidationResult
)


class TestSchemaValidation:
    """Comprehensive tests for input validation schema."""
    
    def test_valid_input_all_fields(self):
        """Test validation with all valid fields."""
        valid_input = {
            "job_key": "book_ingestion_crew",
            "client_user_id": "550e8400-e29b-41d4-a716-446655440000",
            "actor_type": "synth",
            "actor_id": "660e8400-e29b-41d4-a716-446655440001",
            "google_drive_folder_path": "https://drive.google.com/drive/folders/abc123",
            "book_title": "Mi Manuscrito",
            "book_author": "Juan Pérez",
            "language": "es",
            "process_pages_limit": 10
        }
        
        result = validate_book_ingestion_input(valid_input)
        
        assert result.valid is True
        assert result.data is not None
        assert isinstance(result.data, BookIngestionContext)
        assert result.data.book_title == "Mi Manuscrito"
        assert result.data.language == "es"
        assert result.data.process_pages_limit == 10
        assert len(result.errors) == 0
        assert len(result.warnings) == 0
    
    def test_valid_input_minimal_fields(self):
        """Test validation with only required fields."""
        minimal_input = {
            "job_key": "book_ingestion_crew",
            "client_user_id": "550e8400-e29b-41d4-a716-446655440000",
            "actor_type": "client",
            "actor_id": "660e8400-e29b-41d4-a716-446655440001",
            "google_drive_folder_path": "/books/manuscript_001"
        }
        
        result = validate_book_ingestion_input(minimal_input)
        
        assert result.valid is True
        assert result.data is not None
        assert result.data.book_title == "Untitled Book"  # Default value
        assert result.data.book_author == "Unknown Author"  # Default value
        assert result.data.language == "es"  # Default value
        assert result.data.process_pages_limit is None  # Optional, not provided
    
    def test_missing_required_fields(self):
        """Test validation with missing required fields."""
        # Missing client_user_id
        input_missing_client = {
            "job_key": "book_ingestion_crew",
            "actor_type": "synth",
            "actor_id": "660e8400-e29b-41d4-a716-446655440001",
            "google_drive_folder_path": "/books/manuscript_001"
        }
        
        result = validate_book_ingestion_input(input_missing_client)
        
        assert result.valid is False
        assert result.data is None
        assert len(result.errors) > 0
        assert any("client_user_id" in error.field for error in result.errors)
        assert any("required" in error.message.lower() for error in result.errors)
    
    def test_invalid_uuid_format(self):
        """Test validation with invalid UUID formats."""
        invalid_uuid_input = {
            "job_key": "book_ingestion_crew",
            "client_user_id": "not-a-valid-uuid",
            "actor_type": "synth",
            "actor_id": "also-not-a-uuid",
            "google_drive_folder_path": "/books/manuscript_001"
        }
        
        result = validate_book_ingestion_input(invalid_uuid_input)
        
        assert result.valid is False
        assert len(result.errors) >= 2
        uuid_errors = [e for e in result.errors if "uuid" in e.message.lower()]
        assert len(uuid_errors) >= 2
    
    def test_invalid_actor_type(self):
        """Test validation with invalid actor type."""
        invalid_actor_input = {
            "job_key": "book_ingestion_crew",
            "client_user_id": "550e8400-e29b-41d4-a716-446655440000",
            "actor_type": "invalid_type",
            "actor_id": "660e8400-e29b-41d4-a716-446655440001",
            "google_drive_folder_path": "/books/manuscript_001"
        }
        
        result = validate_book_ingestion_input(invalid_actor_input)
        
        assert result.valid is False
        assert any("actor_type" in error.field for error in result.errors)
        assert any("synth" in error.message and "client" in error.message for error in result.errors)
    
    def test_language_validation(self):
        """Test language code validation."""
        # Valid language codes
        valid_languages = ["es", "en", "fr", "de", "it", "pt", "zh", "ja", "ar", "ru"]
        
        for lang in valid_languages:
            input_data = {
                "job_key": "book_ingestion_crew",
                "client_user_id": "550e8400-e29b-41d4-a716-446655440000",
                "actor_type": "synth",
                "actor_id": "660e8400-e29b-41d4-a716-446655440001",
                "google_drive_folder_path": "/books/manuscript_001",
                "language": lang
            }
            
            result = validate_book_ingestion_input(input_data)
            assert result.valid is True, f"Language {lang} should be valid"
            assert result.data.language == lang
        
        # Invalid language code
        invalid_input = {
            "job_key": "book_ingestion_crew",
            "client_user_id": "550e8400-e29b-41d4-a716-446655440000",
            "actor_type": "synth",
            "actor_id": "660e8400-e29b-41d4-a716-446655440001",
            "google_drive_folder_path": "/books/manuscript_001",
            "language": "xx"  # Invalid language code
        }
        
        result = validate_book_ingestion_input(invalid_input)
        assert result.valid is False
        assert any("language" in error.field for error in result.errors)
    
    def test_process_pages_limit_validation(self):
        """Test process_pages_limit validation."""
        # Valid positive limit
        input_valid_limit = {
            "job_key": "book_ingestion_crew",
            "client_user_id": "550e8400-e29b-41d4-a716-446655440000",
            "actor_type": "synth",
            "actor_id": "660e8400-e29b-41d4-a716-446655440001",
            "google_drive_folder_path": "/books/manuscript_001",
            "process_pages_limit": 50
        }
        
        result = validate_book_ingestion_input(input_valid_limit)
        assert result.valid is True
        assert result.data.process_pages_limit == 50
        
        # Zero limit (invalid)
        input_zero_limit = input_valid_limit.copy()
        input_zero_limit["process_pages_limit"] = 0
        
        result = validate_book_ingestion_input(input_zero_limit)
        assert result.valid is False
        assert any("process_pages_limit" in error.field for error in result.errors)
        assert any("positive" in error.message.lower() for error in result.errors)
        
        # Negative limit (invalid)
        input_negative_limit = input_valid_limit.copy()
        input_negative_limit["process_pages_limit"] = -5
        
        result = validate_book_ingestion_input(input_negative_limit)
        assert result.valid is False
        assert any("process_pages_limit" in error.field for error in result.errors)
    
    def test_google_drive_path_formats(self):
        """Test various Google Drive path formats."""
        valid_paths = [
            "https://drive.google.com/drive/folders/abc123def456",
            "/My Drive/Books/Manuscript",
            "Books/Manuscript/2024",
            "manuscript_folder",
            "https://drive.google.com/drive/u/0/folders/abc123"
        ]
        
        for path in valid_paths:
            input_data = {
                "job_key": "book_ingestion_crew",
                "client_user_id": "550e8400-e29b-41d4-a716-446655440000",
                "actor_type": "synth",
                "actor_id": "660e8400-e29b-41d4-a716-446655440001",
                "google_drive_folder_path": path
            }
            
            result = validate_book_ingestion_input(input_data)
            assert result.valid is True, f"Path '{path}' should be valid"
            assert result.data.google_drive_folder_path == path
    
    def test_empty_string_handling(self):
        """Test handling of empty strings for required fields."""
        empty_string_input = {
            "job_key": "book_ingestion_crew",
            "client_user_id": "550e8400-e29b-41d4-a716-446655440000",
            "actor_type": "synth",
            "actor_id": "660e8400-e29b-41d4-a716-446655440001",
            "google_drive_folder_path": ""  # Empty string
        }
        
        result = validate_book_ingestion_input(empty_string_input)
        assert result.valid is False
        assert any("google_drive_folder_path" in error.field for error in result.errors)
    
    def test_extra_fields_ignored(self):
        """Test that extra fields are ignored but don't cause validation failure."""
        input_with_extras = {
            "job_key": "book_ingestion_crew",
            "client_user_id": "550e8400-e29b-41d4-a716-446655440000",
            "actor_type": "synth",
            "actor_id": "660e8400-e29b-41d4-a716-446655440001",
            "google_drive_folder_path": "/books/manuscript_001",
            "extra_field_1": "should be ignored",
            "extra_field_2": 12345,
            "nested_extra": {"key": "value"}
        }
        
        result = validate_book_ingestion_input(input_with_extras)
        assert result.valid is True
        assert result.data is not None
        # Extra fields should not be in the validated data
        assert not hasattr(result.data, 'extra_field_1')
        assert not hasattr(result.data, 'extra_field_2')
        assert not hasattr(result.data, 'nested_extra')
    
    def test_special_characters_in_text_fields(self):
        """Test handling of special characters in text fields."""
        special_chars_input = {
            "job_key": "book_ingestion_crew",
            "client_user_id": "550e8400-e29b-41d4-a716-446655440000",
            "actor_type": "synth",
            "actor_id": "660e8400-e29b-41d4-a716-446655440001",
            "google_drive_folder_path": "/books/manuscript_001",
            "book_title": "El Niño's Adventures: A Story of Café & Crème",
            "book_author": "José María O'Brien-Müller"
        }
        
        result = validate_book_ingestion_input(special_chars_input)
        assert result.valid is True
        assert result.data.book_title == "El Niño's Adventures: A Story of Café & Crème"
        assert result.data.book_author == "José María O'Brien-Müller"
    
    def test_validation_result_structure(self):
        """Test the structure of ValidationResult."""
        valid_input = {
            "job_key": "book_ingestion_crew",
            "client_user_id": "550e8400-e29b-41d4-a716-446655440000",
            "actor_type": "synth",
            "actor_id": "660e8400-e29b-41d4-a716-446655440001",
            "google_drive_folder_path": "/books/manuscript_001"
        }
        
        result = validate_book_ingestion_input(valid_input)
        
        # Check ValidationResult attributes
        assert hasattr(result, 'valid')
        assert hasattr(result, 'data')
        assert hasattr(result, 'errors')
        assert hasattr(result, 'warnings')
        
        assert isinstance(result.valid, bool)
        assert isinstance(result.errors, list)
        assert isinstance(result.warnings, list)
        
        # For valid input
        assert result.valid is True
        assert result.data is not None
        assert len(result.errors) == 0
    
    def test_type_coercion(self):
        """Test type coercion for numeric fields."""
        # String number for process_pages_limit
        input_string_number = {
            "job_key": "book_ingestion_crew",
            "client_user_id": "550e8400-e29b-41d4-a716-446655440000",
            "actor_type": "synth",
            "actor_id": "660e8400-e29b-41d4-a716-446655440001",
            "google_drive_folder_path": "/books/manuscript_001",
            "process_pages_limit": "25"  # String instead of int
        }
        
        result = validate_book_ingestion_input(input_string_number)
        assert result.valid is True
        assert result.data.process_pages_limit == 25  # Should be coerced to int
        
        # Invalid string for numeric field
        input_invalid_string = input_string_number.copy()
        input_invalid_string["process_pages_limit"] = "not a number"
        
        result = validate_book_ingestion_input(input_invalid_string)
        assert result.valid is False
        assert any("process_pages_limit" in error.field for error in result.errors)


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])