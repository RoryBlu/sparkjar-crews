#!/usr/bin/env python3
"""
Example usage of SyncDBStorageTool for book ingestion.

This example demonstrates how to use the SyncDBStorageTool in a CrewAI crew
for storing transcribed book pages to the database.
"""
import json
import uuid
from sync_db_storage_tool import SyncDBStorageTool


def example_basic_usage():
    """Basic usage example with all required parameters."""
    print("=== Basic Usage Example ===")
    
    tool = SyncDBStorageTool()
    
    # Example parameters as would come from the book ingestion crew
    params = {
        "client_user_id": "550e8400-e29b-41d4-a716-446655440000",  # Example UUID
        "book_key": "hemingway_old_man_sea_manuscript",
        "page_number": 1,  # Explicitly provided
        "file_name": "page_001.jpg",
        "language_code": "en",
        "page_text": """The Old Man and the Sea
        
Chapter 1

He was an old man who fished alone in a skiff in the Gulf Stream and he had gone eighty-four days now without taking a fish.""",
        "ocr_metadata": {
            "file_id": "1BxYz9K3mN8pQ2rS4tU6vW7xY8zA9bC0d",
            "processing_stats": {
                "total_words": 35,
                "normal_transcription": 32,
                "context_logic_transcription": 3,
                "unable_to_transcribe": 0
            },
            "unclear_sections": [],
            "ocr_passes": 3,
            "model_used": "gpt-4o"
        }
    }
    
    # Execute the tool
    result_str = tool._run(**params)
    result = json.loads(result_str)
    
    print(f"Result: {json.dumps(result, indent=2)}")
    return result


def example_auto_page_extraction():
    """Example with automatic page number extraction from filename."""
    print("\n=== Auto Page Number Extraction Example ===")
    
    tool = SyncDBStorageTool()
    
    # Example without explicit page_number - will be extracted from filename
    params = {
        "client_user_id": "550e8400-e29b-41d4-a716-446655440000",
        "book_key": "scientific_journal_1923",
        "file_name": "manuscript_page_042.tiff",  # Page number will be extracted
        "language_code": "en",
        "page_text": """Journal of Theoretical Physics
Volume 15, Issue 3, March 1923

On the Quantum Theory of Radiation

By A. Einstein""",
        "ocr_metadata": {
            "file_id": "2CyZa0L4oP9qR3sT5uV7wX8yZ9aB0cD1e",
            "processing_stats": {
                "total_words": 18,
                "normal_transcription": 18,
                "context_logic_transcription": 0,
                "unable_to_transcribe": 0
            },
            "unclear_sections": [],
            "ocr_passes": 3,
            "model_used": "gpt-4o"
        },
        "version": "original"
    }
    
    # Show page number extraction
    extracted_page = tool._extract_page_number_from_filename(params["file_name"])
    print(f"Extracted page number: {extracted_page}")
    
    # Execute the tool
    result_str = tool._run(**params)
    result = json.loads(result_str)
    
    print(f"Result: {json.dumps(result, indent=2)}")
    return result


def example_multilingual():
    """Example with multilingual content."""
    print("\n=== Multilingual Content Example ===")
    
    tool = SyncDBStorageTool()
    
    params = {
        "client_user_id": "550e8400-e29b-41d4-a716-446655440000",
        "book_key": "garcia_marquez_solitude_manuscript",
        "file_name": "pagina_025.png",
        "language_code": "es",
        "page_text": """Cien Años de Soledad

Capítulo 2

Muchos años después, frente al pelotón de fusilamiento, el coronel Aureliano Buendía había de recordar aquella tarde remota en que su padre lo llevó a conocer el hielo.""",
        "ocr_metadata": {
            "file_id": "3DzAb1M5pQ0rS4tU6vW7xY8zA9bC0dE2f",
            "processing_stats": {
                "total_words": 32,
                "normal_transcription": 28,
                "context_logic_transcription": 4,
                "unable_to_transcribe": 0
            },
            "unclear_sections": ["palabra borrosa cerca de 'pelotón'"],
            "ocr_passes": 3,
            "model_used": "gpt-4o",
            "language_detected": "spanish"
        }
    }
    
    result_str = tool._run(**params)
    result = json.loads(result_str)
    
    print(f"Result: {json.dumps(result, indent=2)}")
    return result


def example_crewai_integration():
    """Example showing how to integrate with CrewAI agents."""
    print("\n=== CrewAI Integration Example ===")
    
    # This is how the tool would be used in a CrewAI agent
    print("""
# In your CrewAI agent configuration (agents.yaml):
storage_agent:
  role: "Data Storage Specialist"
  goal: "Store transcribed pages in database"
  backstory: "Efficiently stores OCR results with proper error handling"
  model: "gpt-4.1-nano"
  tools:
    - SyncDBStorageTool

# In your CrewAI task configuration (tasks.yaml):
storage_task:
  description: "Store the transcribed page using SyncDBStorageTool with parameters: {storage_params}"
  expected_output: "JSON confirmation with page_id and storage status"
  agent: storage_agent
  context: [ocr_task]
    """)
    
    # Example of how the agent would call the tool
    tool = SyncDBStorageTool()
    
    # Parameters that would come from previous tasks in the crew
    storage_params = {
        "client_user_id": "550e8400-e29b-41d4-a716-446655440000",
        "book_key": "book_ingestion_test",
        "file_name": "scan_001.jpg",
        "language_code": "en",
        "page_text": "Sample transcribed text from OCR processing...",
        "ocr_metadata": {
            "file_id": "google_drive_file_id_123",
            "processing_stats": {"total_words": 10},
            "ocr_passes": 3,
            "model_used": "gpt-4o"
        }
    }
    
    print("Agent would call:")
    print(f"tool._run(**{storage_params})")
    
    result_str = tool._run(**storage_params)
    result = json.loads(result_str)
    
    print(f"\nAgent would receive: {json.dumps(result, indent=2)}")
    return result


def main():
    """Run all examples."""
    print("SyncDBStorageTool Usage Examples")
    print("=" * 50)
    
    examples = [
        example_basic_usage,
        example_auto_page_extraction,
        example_multilingual,
        example_crewai_integration,
    ]
    
    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"Example {example.__name__} failed: {e}")
    
    print("\n" + "=" * 50)
    print("All examples completed!")
    print("\nNote: These examples will show database connection errors")
    print("since no actual database is configured, but they demonstrate")
    print("the correct usage patterns and input validation.")


if __name__ == "__main__":
    main()