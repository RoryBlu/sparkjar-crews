"""
Example demonstrating the book ingestion crew input validation features.
This shows how to use the Pydantic schema validation with comprehensive error handling.
"""

from uuid import uuid4
from .schema import (
    validate_book_ingestion_input,
    get_supported_languages,
    validate_language_code,
    BookIngestionRequest
)


def demonstrate_validation():
    """Demonstrate various validation scenarios."""
    
    print("=== Book Ingestion Crew Input Validation Demo ===\n")
    
    # 1. Valid input example
    print("1. Valid Input Example:")
    valid_data = {
        "job_key": "book_ingestion_crew",
        "client_user_id": str(uuid4()),
        "actor_type": "client",
        "actor_id": str(uuid4()),
        "google_drive_folder_path": "https://drive.google.com/drive/folders/1ABC123DEF456",
        "book_title": "My Handwritten Manuscript",
        "book_author": "John Doe",
        "book_description": "A collection of handwritten notes and stories",
        "language": "en",
        "process_pages_limit": 10
    }
    
    result = validate_book_ingestion_input(valid_data)
    print(f"✅ Valid: {result.valid}")
    print(f"   Errors: {len(result.errors)}")
    print(f"   Data keys: {list(result.data.keys()) if result.data else 'None'}")
    print()
    
    # 2. Invalid input with detailed errors
    print("2. Invalid Input Example:")
    invalid_data = {
        "job_key": "wrong_job_key",
        "client_user_id": "invalid-uuid",
        "actor_type": "invalid_actor",
        "actor_id": "also-invalid-uuid",
        "google_drive_folder_path": "",
        "book_title": "   ",  # Empty after whitespace removal
        "book_author": "",
        "language": "invalid_lang",
        "process_pages_limit": -5
    }
    
    result = validate_book_ingestion_input(invalid_data)
    print(f"❌ Valid: {result.valid}")
    print(f"   Errors: {len(result.errors)}")
    for error in result.errors:
        print(f"   - {error.field}: {error.message}")
    print(f"   Error Summary: {result.error_summary}")
    print()
    
    # 3. Language validation examples
    print("3. Language Validation:")
    supported_languages = get_supported_languages()
    print(f"   Supported languages: {list(supported_languages.keys())}")
    
    # Test valid languages
    valid_languages = ["en", "es", "fr", "de"]
    for lang in valid_languages:
        is_valid = validate_language_code(lang)
        lang_name = supported_languages.get(lang, "Unknown")
        print(f"   ✅ {lang} ({lang_name}): {is_valid}")
    
    # Test invalid languages
    invalid_languages = ["invalid", "english", "xx"]
    for lang in invalid_languages:
        is_valid = validate_language_code(lang)
        print(f"   ❌ {lang}: {is_valid}")
    print()
    
    # 4. Google Drive path validation
    print("4. Google Drive Path Validation:")
    test_paths = [
        "https://drive.google.com/drive/folders/1ABC123DEF456",
        "https://drive.google.com/drive/u/0/folders/1ABC123DEF456", 
        "1ABC123DEF456",  # Direct folder ID
        "/path/to/folder",  # Path format
        "",  # Invalid - empty
        "invalid-url",  # Invalid format
    ]
    
    for path in test_paths:
        test_data = valid_data.copy()
        test_data["google_drive_folder_path"] = path
        result = validate_book_ingestion_input(test_data)
        status = "✅" if result.valid else "❌"
        print(f"   {status} '{path}': {result.valid}")
        if not result.valid:
            path_errors = [e for e in result.errors if e.field == "google_drive_folder_path"]
            if path_errors:
                print(f"      Error: {path_errors[0].message}")
    print()
    
    # 5. Process pages limit validation
    print("5. Process Pages Limit Validation:")
    test_limits = [None, 0, 1, 10, 100, -1, -10]
    
    for limit in test_limits:
        test_data = valid_data.copy()
        if limit is not None:
            test_data["process_pages_limit"] = limit
        else:
            test_data.pop("process_pages_limit", None)
        
        result = validate_book_ingestion_input(test_data)
        status = "✅" if result.valid else "❌"
        print(f"   {status} limit={limit}: {result.valid}")
        if not result.valid:
            limit_errors = [e for e in result.errors if e.field == "process_pages_limit"]
            if limit_errors:
                print(f"      Error: {limit_errors[0].message}")
    print()
    
    # 6. Direct Pydantic model usage
    print("6. Direct Pydantic Model Usage:")
    try:
        model = BookIngestionRequest(**valid_data)
        print(f"✅ Model created successfully")
        print(f"   Job Key: {model.job_key}")
        print(f"   Language: {model.language}")
        print(f"   Book Title: {model.book_title}")
        print(f"   Process Pages Limit: {model.process_pages_limit}")
    except Exception as e:
        print(f"❌ Model creation failed: {e}")
    print()
    
    # 7. Text cleaning examples
    print("7. Text Cleaning Examples:")
    messy_texts = [
        "  Title with spaces  ",
        "Title\twith\ttabs",
        "Title\nwith\nnewlines",
        "Multiple   spaces   between   words"
    ]
    
    for messy_text in messy_texts:
        test_data = valid_data.copy()
        test_data["book_title"] = messy_text
        result = validate_book_ingestion_input(test_data)
        if result.valid and result.data:
            cleaned_title = result.data["book_title"]
            print(f"   '{messy_text}' → '{cleaned_title}'")
    print()
    
    print("=== Validation Demo Complete ===")


if __name__ == "__main__":
    demonstrate_validation()