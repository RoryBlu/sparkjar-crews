"""
Unit tests for book ingestion crew input validation schema.
Tests all validation scenarios including edge cases and error handling.
"""

import pytest
from uuid import uuid4, UUID
from typing import Dict, Any

from .schema import (
    BookIngestionRequest,
    ActorType,
    LanguageCode,
    validate_book_ingestion_input,
    get_supported_languages,
    validate_language_code,
    BookIngestionValidationResult
)


class TestBookIngestionRequest:
    """Test cases for BookIngestionRequest Pydantic model."""
    
    def get_valid_input(self) -> Dict[str, Any]:
        """Get a valid input dictionary for testing."""
        return {
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
    
    def test_valid_input_complete(self):
        """Test validation with all valid fields provided."""
        data = self.get_valid_input()
        model = BookIngestionRequest(**data)
        
        assert model.job_key == "book_ingestion_crew"
        assert model.client_user_id == UUID(data["client_user_id"])
        assert model.actor_type == ActorType.CLIENT
        assert model.actor_id == UUID(data["actor_id"])
        assert model.google_drive_folder_path == data["google_drive_folder_path"]
        assert model.book_title == "Test Manuscript"
        assert model.book_author == "Test Author"
        assert model.book_description == "A test manuscript for validation"
        assert model.language == LanguageCode.ENGLISH
        assert model.process_pages_limit == 10
    
    def test_valid_input_minimal(self):
        """Test validation with only required fields."""
        data = {
            "job_key": "book_ingestion_crew",
            "client_user_id": str(uuid4()),
            "actor_type": "synth",
            "actor_id": str(uuid4()),
            "google_drive_folder_path": "1ABC123DEF456",
            "book_title": "Minimal Test",
            "book_author": "Author",
            "language": "es"
        }
        
        model = BookIngestionRequest(**data)
        assert model.book_description is None
        assert model.process_pages_limit is None
        assert model.language == LanguageCode.SPANISH
    
    def test_missing_required_fields(self):
        """Test validation fails when required fields are missing."""
        data = self.get_valid_input()
        
        required_fields = [
            "client_user_id", "actor_type", "actor_id", 
            "google_drive_folder_path", "book_title", "book_author", "language"
        ]
        
        for field in required_fields:
            test_data = data.copy()
            del test_data[field]
            
            with pytest.raises(ValueError) as exc_info:
                BookIngestionRequest(**test_data)
            
            assert "field required" in str(exc_info.value).lower()
    
    def test_invalid_uuid_fields(self):
        """Test validation fails for invalid UUID fields."""
        data = self.get_valid_input()
        
        # Test invalid client_user_id
        data["client_user_id"] = "invalid-uuid"
        with pytest.raises(ValueError) as exc_info:
            BookIngestionRequest(**data)
        assert "invalid" in str(exc_info.value).lower()
        
        # Test invalid actor_id
        data = self.get_valid_input()
        data["actor_id"] = "not-a-uuid"
        with pytest.raises(ValueError) as exc_info:
            BookIngestionRequest(**data)
        assert "invalid" in str(exc_info.value).lower()
    
    def test_invalid_actor_type(self):
        """Test validation fails for invalid actor types."""
        data = self.get_valid_input()
        data["actor_type"] = "invalid_actor"
        
        with pytest.raises(ValueError) as exc_info:
            BookIngestionRequest(**data)
        assert "not a valid enumeration member" in str(exc_info.value).lower()
    
    def test_invalid_language_code(self):
        """Test validation fails for unsupported language codes."""
        data = self.get_valid_input()
        data["language"] = "invalid_lang"
        
        with pytest.raises(ValueError) as exc_info:
            BookIngestionRequest(**data)
        assert "not a valid enumeration member" in str(exc_info.value).lower()
    
    def test_google_drive_path_validation(self):
        """Test Google Drive path validation with various formats."""
        data = self.get_valid_input()
        
        # Valid formats
        valid_paths = [
            "https://drive.google.com/drive/folders/1ABC123DEF456",
            "https://drive.google.com/drive/u/0/folders/1ABC123DEF456",
            "1ABC123DEF456",  # Direct folder ID
            "/path/to/folder"  # Path format
        ]
        
        for path in valid_paths:
            test_data = data.copy()
            test_data["google_drive_folder_path"] = path
            model = BookIngestionRequest(**test_data)
            assert model.google_drive_folder_path == path
        
        # Invalid formats
        invalid_paths = [
            "",  # Empty
            "   ",  # Whitespace only
            "invalid-url",
            "http://not-google-drive.com/folder"
        ]
        
        for path in invalid_paths:
            test_data = data.copy()
            test_data["google_drive_folder_path"] = path
            with pytest.raises(ValueError) as exc_info:
                BookIngestionRequest(**test_data)
            assert "Google Drive folder path" in str(exc_info.value)
    
    def test_book_title_validation(self):
        """Test book title validation and cleaning."""
        data = self.get_valid_input()
        
        # Valid titles with whitespace cleaning
        test_cases = [
            ("  Title with spaces  ", "Title with spaces"),
            ("Title\twith\ttabs", "Title with tabs"),
            ("Title\nwith\nnewlines", "Title with newlines"),
            ("Multiple   spaces   between", "Multiple spaces between")
        ]
        
        for input_title, expected_title in test_cases:
            test_data = data.copy()
            test_data["book_title"] = input_title
            model = BookIngestionRequest(**test_data)
            assert model.book_title == expected_title
        
        # Invalid titles
        invalid_titles = ["", "   ", "\t\n  "]
        
        for title in invalid_titles:
            test_data = data.copy()
            test_data["book_title"] = title
            with pytest.raises(ValueError) as exc_info:
                BookIngestionRequest(**test_data)
            assert "cannot be empty" in str(exc_info.value)
    
    def test_book_author_validation(self):
        """Test book author validation and cleaning."""
        data = self.get_valid_input()
        
        # Valid authors with whitespace cleaning
        test_cases = [
            ("  John Doe  ", "John Doe"),
            ("Jane\tSmith", "Jane Smith"),
            ("Author\nName", "Author Name")
        ]
        
        for input_author, expected_author in test_cases:
            test_data = data.copy()
            test_data["book_author"] = input_author
            model = BookIngestionRequest(**test_data)
            assert model.book_author == expected_author
        
        # Invalid authors
        invalid_authors = ["", "   ", "\t\n  "]
        
        for author in invalid_authors:
            test_data = data.copy()
            test_data["book_author"] = author
            with pytest.raises(ValueError) as exc_info:
                BookIngestionRequest(**test_data)
            assert "cannot be empty" in str(exc_info.value)
    
    def test_book_description_validation(self):
        """Test book description validation and cleaning."""
        data = self.get_valid_input()
        
        # Valid descriptions
        test_data = data.copy()
        test_data["book_description"] = "  A valid description  "
        model = BookIngestionRequest(**test_data)
        assert model.book_description == "A valid description"
        
        # Empty description should become None
        test_data["book_description"] = "   "
        model = BookIngestionRequest(**test_data)
        assert model.book_description is None
        
        # None description
        test_data["book_description"] = None
        model = BookIngestionRequest(**test_data)
        assert model.book_description is None
    
    def test_process_pages_limit_validation(self):
        """Test process pages limit validation."""
        data = self.get_valid_input()
        
        # Valid limits
        valid_limits = [0, 1, 10, 100, None]
        
        for limit in valid_limits:
            test_data = data.copy()
            test_data["process_pages_limit"] = limit
            model = BookIngestionRequest(**test_data)
            assert model.process_pages_limit == limit
        
        # Invalid limits
        invalid_limits = [-1, -10]
        
        for limit in invalid_limits:
            test_data = data.copy()
            test_data["process_pages_limit"] = limit
            with pytest.raises(ValueError) as exc_info:
                BookIngestionRequest(**test_data)
            assert "must be 0 or greater" in str(exc_info.value)
    
    def test_extra_fields_forbidden(self):
        """Test that extra fields are forbidden."""
        data = self.get_valid_input()
        data["extra_field"] = "should not be allowed"
        
        with pytest.raises(ValueError) as exc_info:
            BookIngestionRequest(**data)
        assert "extra fields not permitted" in str(exc_info.value).lower()


class TestValidationFunction:
    """Test cases for the validate_book_ingestion_input function."""
    
    def get_valid_input(self) -> Dict[str, Any]:
        """Get a valid input dictionary for testing."""
        return {
            "job_key": "book_ingestion_crew",
            "client_user_id": str(uuid4()),
            "actor_type": "client",
            "actor_id": str(uuid4()),
            "google_drive_folder_path": "https://drive.google.com/drive/folders/1ABC123DEF456",
            "book_title": "Test Manuscript",
            "book_author": "Test Author",
            "language": "en"
        }
    
    def test_valid_input_success(self):
        """Test successful validation with valid input."""
        data = self.get_valid_input()
        result = validate_book_ingestion_input(data)
        
        assert result.valid is True
        assert result.data is not None
        assert len(result.errors) == 0
        assert len(result.warnings) == 0
        assert result.error_summary == "No validation errors"
    
    def test_invalid_input_detailed_errors(self):
        """Test validation failure with detailed error information."""
        data = {
            "job_key": "wrong_job_key",
            "client_user_id": "invalid-uuid",
            "actor_type": "invalid_actor",
            "google_drive_folder_path": "",
            "book_title": "",
            "book_author": "",
            "language": "invalid_lang"
        }
        
        result = validate_book_ingestion_input(data)
        
        assert result.valid is False
        assert result.data is None
        assert len(result.errors) > 0
        
        # Check that we have detailed error information
        error_fields = [error.field for error in result.errors]
        assert "client_user_id" in error_fields
        assert "actor_type" in error_fields
        assert "google_drive_folder_path" in error_fields
        assert "book_title" in error_fields
        assert "book_author" in error_fields
        assert "language" in error_fields
        
        # Check error summary
        assert "No validation errors" not in result.error_summary
        assert len(result.error_summary) > 0
    
    def test_missing_required_fields(self):
        """Test validation with missing required fields."""
        data = {"job_key": "book_ingestion_crew"}
        
        result = validate_book_ingestion_input(data)
        
        assert result.valid is False
        assert len(result.errors) > 0
        
        # Check for missing field errors
        error_messages = [error.message for error in result.errors]
        assert any("field required" in msg.lower() for msg in error_messages)
    
    def test_unexpected_error_handling(self):
        """Test handling of unexpected validation errors."""
        # This test simulates an unexpected error scenario
        # In practice, this might be hard to trigger with Pydantic
        # but we test the error handling structure
        
        result = validate_book_ingestion_input(None)
        
        assert result.valid is False
        assert len(result.errors) > 0
        assert result.errors[0].field == "general"
        assert "Unexpected validation error" in result.errors[0].message


class TestLanguageSupport:
    """Test cases for language support functions."""
    
    def test_get_supported_languages(self):
        """Test getting supported languages mapping."""
        languages = get_supported_languages()
        
        assert isinstance(languages, dict)
        assert len(languages) > 0
        
        # Check some expected languages
        expected_languages = {
            "en": "English",
            "es": "Spanish",
            "fr": "French",
            "de": "German"
        }
        
        for code, name in expected_languages.items():
            assert code in languages
            assert languages[code] == name
    
    def test_validate_language_code(self):
        """Test language code validation function."""
        # Valid language codes
        valid_codes = ["en", "es", "fr", "de", "it", "pt"]
        for code in valid_codes:
            assert validate_language_code(code) is True
            assert validate_language_code(code.upper()) is True  # Case insensitive
        
        # Invalid language codes
        invalid_codes = ["invalid", "xx", "english", ""]
        for code in invalid_codes:
            assert validate_language_code(code) is False
    
    def test_language_enum_completeness(self):
        """Test that LanguageCode enum matches supported languages."""
        supported_languages = get_supported_languages()
        enum_values = [lang.value for lang in LanguageCode]
        
        # All enum values should be in supported languages
        for enum_value in enum_values:
            assert enum_value in supported_languages
        
        # All supported languages should have enum values
        for lang_code in supported_languages.keys():
            assert lang_code in enum_values


class TestValidationResult:
    """Test cases for BookIngestionValidationResult model."""
    
    def test_validation_result_creation(self):
        """Test creating validation result objects."""
        # Successful result
        success_result = BookIngestionValidationResult(
            valid=True,
            data={"test": "data"},
            errors=[],
            warnings=[]
        )
        
        assert success_result.valid is True
        assert success_result.data == {"test": "data"}
        assert len(success_result.errors) == 0
        assert success_result.error_summary == "No validation errors"
        
        # Failed result with errors
        from .schema import ValidationErrorDetail
        
        error_detail = ValidationErrorDetail(
            field="test_field",
            message="Test error message",
            invalid_value="invalid",
            error_type="test_error"
        )
        
        failed_result = BookIngestionValidationResult(
            valid=False,
            data=None,
            errors=[error_detail],
            warnings=["Test warning"]
        )
        
        assert failed_result.valid is False
        assert failed_result.data is None
        assert len(failed_result.errors) == 1
        assert failed_result.error_summary == "test_field: Test error message"


if __name__ == "__main__":
    pytest.main([__file__])