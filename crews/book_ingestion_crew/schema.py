"""
Book Ingestion Crew Schema
Defines the input schema for the book ingestion crew using both Pydantic and JSON Schema.
"""

from typing import Optional, Dict, Any, List, Literal
from uuid import UUID
from enum import Enum
import re

from pydantic import BaseModel, Field, field_validator, ValidationError, ConfigDict


class ActorType(str, Enum):
    """Valid actor types for book ingestion requests."""
    SYNTH = "synth"
    HUMAN = "human"
    SYNTH_CLASS = "synth_class"
    CLIENT = "client"


class LanguageCode(str, Enum):
    """Supported language codes with ISO 639-1 format."""
    SPANISH = "es"
    ENGLISH = "en"
    PORTUGUESE = "pt"
    FRENCH = "fr"
    ITALIAN = "it"
    GERMAN = "de"
    DUTCH = "nl"
    POLISH = "pl"
    RUSSIAN = "ru"
    JAPANESE = "ja"
    CHINESE = "zh"


class BookIngestionRequest(BaseModel):
    """
    Pydantic model for book ingestion crew input validation.
    
    This model provides comprehensive validation with detailed error messages
    for all required and optional fields in the book ingestion process.
    """
    
    job_key: Literal["book_ingestion_crew"] = Field(
        default="book_ingestion_crew",
        description="Job key identifier for the book ingestion crew"
    )
    
    client_user_id: UUID = Field(
        ...,
        description="UUID of the client user requesting the book ingestion"
    )
    
    actor_type: ActorType = Field(
        ...,
        description="Type of actor performing the request (synth, human, synth_class, client)"
    )
    
    actor_id: UUID = Field(
        ...,
        description="UUID of the specific actor performing the request"
    )
    
    google_drive_folder_path: str = Field(
        ...,
        min_length=1,
        description="Google Drive folder path, URL, or folder ID containing manuscript images"
    )
    
    book_title: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Title of the book being ingested"
    )
    
    book_author: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Author of the book being ingested"
    )
    
    book_description: Optional[str] = Field(
        None,
        max_length=2000,
        description="Optional description of the book content"
    )
    
    language: LanguageCode = Field(
        ...,
        description="Language code for the manuscript content (ISO 639-1 format)"
    )
    
    process_pages_limit: Optional[int] = Field(
        None,
        ge=0,
        description="Optional limit on number of pages to process (0 or None means process all pages)"
    )
    
    @field_validator('google_drive_folder_path')
    @classmethod
    def validate_google_drive_path(cls, v):
        """Validate Google Drive folder path format."""
        if not v or not v.strip():
            raise ValueError("Google Drive folder path cannot be empty")
        
        # Check for common Google Drive URL patterns
        drive_patterns = [
            r'https://drive\.google\.com/drive/folders/[a-zA-Z0-9_-]+',
            r'https://drive\.google\.com/drive/u/\d+/folders/[a-zA-Z0-9_-]+',
            r'^[a-zA-Z0-9_-]+$',  # Direct folder ID
            r'^/.*',  # Path format
        ]
        
        if not any(re.match(pattern, v.strip()) for pattern in drive_patterns):
            raise ValueError(
                "Google Drive folder path must be a valid URL, folder ID, or path format. "
                "Examples: 'https://drive.google.com/drive/folders/1ABC...', '1ABC123...', or '/path/to/folder'"
            )
        
        return v.strip()
    
    @field_validator('book_title')
    @classmethod
    def validate_book_title(cls, v):
        """Validate book title format."""
        if not v or not v.strip():
            raise ValueError("Book title cannot be empty")
        
        # Remove excessive whitespace
        cleaned = ' '.join(v.split())
        
        if len(cleaned) < 1:
            raise ValueError("Book title must contain at least one non-whitespace character")
        
        return cleaned
    
    @field_validator('book_author')
    @classmethod
    def validate_book_author(cls, v):
        """Validate book author format."""
        if not v or not v.strip():
            raise ValueError("Book author cannot be empty")
        
        # Remove excessive whitespace
        cleaned = ' '.join(v.split())
        
        if len(cleaned) < 1:
            raise ValueError("Book author must contain at least one non-whitespace character")
        
        return cleaned
    
    @field_validator('book_description')
    @classmethod
    def validate_book_description(cls, v):
        """Validate book description if provided."""
        if v is not None:
            # Remove excessive whitespace
            cleaned = ' '.join(v.split()) if v else None
            return cleaned if cleaned else None
        return v
    
    @field_validator('process_pages_limit')
    @classmethod
    def validate_process_pages_limit(cls, v):
        """Validate process pages limit."""
        if v is not None and v < 0:
            raise ValueError("Process pages limit must be 0 or greater (0 means process all pages)")
        return v
    
    model_config = ConfigDict(
        use_enum_values=True,
        validate_assignment=True,
        extra="forbid",  # Forbid additional properties
        json_schema_extra={
            "example": {
                "job_key": "book_ingestion_crew",
                "client_user_id": "123e4567-e89b-12d3-a456-426614174000",
                "actor_type": "client",
                "actor_id": "123e4567-e89b-12d3-a456-426614174001",
                "google_drive_folder_path": "https://drive.google.com/drive/folders/1ABC123DEF456",
                "book_title": "My Handwritten Manuscript",
                "book_author": "John Doe",
                "book_description": "A collection of handwritten notes and stories",
                "language": "en",
                "process_pages_limit": 10
            }
        }
    )


class ValidationErrorDetail(BaseModel):
    """Detailed validation error information."""
    field: str
    message: str
    invalid_value: Any
    error_type: str


class BookIngestionValidationResult(BaseModel):
    """Result of book ingestion input validation."""
    valid: bool
    data: Optional[Dict[str, Any]] = None
    errors: List[ValidationErrorDetail] = []
    warnings: List[str] = []
    
    @property
    def error_summary(self) -> str:
        """Get a summary of all validation errors."""
        if not self.errors:
            return "No validation errors"
        
        error_messages = [f"{error.field}: {error.message}" for error in self.errors]
        return "; ".join(error_messages)


def validate_book_ingestion_input(data: Dict[str, Any]) -> BookIngestionValidationResult:
    """
    Validate book ingestion input data using Pydantic model.
    
    Args:
        data: Input data dictionary to validate
        
    Returns:
        BookIngestionValidationResult with validation status and details
    """
    try:
        # Attempt to create and validate the Pydantic model
        validated_model = BookIngestionRequest(**data)
        
        # Convert back to dict for compatibility
        validated_data = validated_model.model_dump()
        
        return BookIngestionValidationResult(
            valid=True,
            data=validated_data,
            errors=[],
            warnings=[]
        )
        
    except ValidationError as e:
        # Extract detailed error information
        errors = []
        for error in e.errors():
            field_path = ".".join(str(loc) for loc in error["loc"])
            errors.append(ValidationErrorDetail(
                field=field_path,
                message=error["msg"],
                invalid_value=error.get("input", "N/A"),
                error_type=error["type"]
            ))
        
        return BookIngestionValidationResult(
            valid=False,
            data=None,
            errors=errors,
            warnings=[]
        )
    
    except Exception as e:
        # Handle unexpected validation errors
        errors = [ValidationErrorDetail(
            field="general",
            message=f"Unexpected validation error: {str(e)}",
            invalid_value=data,
            error_type="unexpected_error"
        )]
        
        return BookIngestionValidationResult(
            valid=False,
            data=None,
            errors=errors,
            warnings=[]
        )


def get_supported_languages() -> Dict[str, str]:
    """
    Get mapping of supported language codes to language names.
    
    Returns:
        Dictionary mapping language codes to language names
    """
    return {
        "es": "Spanish",
        "en": "English", 
        "pt": "Portuguese",
        "fr": "French",
        "it": "Italian",
        "de": "German",
        "nl": "Dutch",
        "pl": "Polish",
        "ru": "Russian",
        "ja": "Japanese",
        "zh": "Chinese"
    }


def validate_language_code(language_code: str) -> bool:
    """
    Validate if a language code is supported.
    
    Args:
        language_code: Language code to validate
        
    Returns:
        True if language code is supported, False otherwise
    """
    supported_languages = get_supported_languages()
    return language_code.lower() in supported_languages


# Legacy JSON Schema for backward compatibility
BOOK_INGESTION_SCHEMA = {
    "type": "object",
    "properties": {
        "job_key": {
            "type": "string",
            "const": "book_ingestion_crew"
        },
        "client_user_id": {
            "type": "string",
            "format": "uuid"
        },
        "actor_type": {
            "type": "string",
            "enum": ["synth", "human", "synth_class", "client"]
        },
        "actor_id": {
            "type": "string",
            "format": "uuid"
        },
        "google_drive_folder_path": {
            "type": "string",
            "description": "Google Drive folder path, URL, or folder ID"
        },
        "book_title": {
            "type": "string",
            "minLength": 1,
            "maxLength": 500
        },
        "book_author": {
            "type": "string",
            "minLength": 1,
            "maxLength": 200
        },
        "book_description": {
            "type": "string",
            "maxLength": 2000
        },
        "language": {
            "type": "string",
            "enum": ["es", "en", "pt", "fr", "it", "de", "nl", "pl", "ru", "ja", "zh"]
        },
        "process_pages_limit": {
            "type": "integer",
            "minimum": 0,
            "description": "0 means process all pages"
        }
    },
    "required": [
        "job_key",
        "client_user_id", 
        "actor_type",
        "actor_id",
        "google_drive_folder_path",
        "book_title",
        "book_author",
        "language"
    ],
    "additionalProperties": False
}