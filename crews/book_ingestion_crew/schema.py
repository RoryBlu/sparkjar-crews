"""
Book Ingestion Crew Schema
Defines the input schema for the book ingestion crew.
"""

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
            "minLength": 1
        },
        "book_author": {
            "type": "string",
            "minLength": 1
        },
        "book_description": {
            "type": "string"
        },
        "language": {
            "type": "string",
            "enum": ["Spanish", "English", "Portuguese", "French", "Italian", "German"]
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
    "additionalProperties": false
}