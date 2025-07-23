# Book Ingestion Crew

## Introduction

The Book Ingestion Crew is a CrewAI-based system designed to process handwritten manuscript images from Google Drive folders. It performs high-quality OCR (Optical Character Recognition) using GPT-4o's vision capabilities and stores the transcribed text in a PostgreSQL database. The crew is optimized for processing historical manuscripts, personal notebooks, and other handwritten documents.

## Features

- **Google Drive Integration**: Seamlessly lists and downloads images from Google Drive folders
- **Multi-Format Support**: Processes PNG, JPG, JPEG, WEBP, GIF, BMP, and TIFF image formats
- **3-Pass OCR**: Uses GPT-4o vision model with three passes for maximum accuracy
- **Sequential Processing**: Downloads and processes files one at a time to avoid memory issues
- **Multi-Language Support**: Configurable language support via input parameters
- **Database Storage**: Stores transcriptions in BookIngestions table with metadata
- **Progress Tracking**: Provides detailed progress updates during processing

## Requirements

### Requirement 1: Google Drive Processing

**User Story:** As a content manager, I want to process manuscript images from Google Drive, so that I can digitize handwritten books into searchable text format.

#### Acceptance Criteria
1. WHEN a Google Drive folder URL is provided THEN the system SHALL list all image files in the folder
2. WHEN processing begins THEN the system SHALL download files one at a time sequentially
3. WHEN an image is downloaded THEN the system SHALL support PNG, JPG, JPEG, WEBP, GIF, BMP, and TIFF formats
4. WHEN processing completes THEN the system SHALL store transcribed pages in the BookIngestions database table

### Requirement 2: OCR Quality

**User Story:** As a quality assurance specialist, I want OCR processing with multiple passes, so that I can ensure accurate text transcription from handwritten manuscripts.

#### Acceptance Criteria
1. WHEN an image is processed THEN the system SHALL perform exactly 3 OCR passes using GPT-4o
2. WHEN OCR processing occurs THEN the system SHALL capture the complete page content including the top 4-5 lines
3. WHEN processing a page THEN the system SHALL use a maximum of 4 LLM calls (1 coordination + 3 OCR passes)
4. WHEN OCR completes THEN the system SHALL store the transcribed text with metadata including file_id and processing stats

## Usage

### Direct Execution
```bash
python crews/book_ingestion_crew/main.py \
  --folder "https://drive.google.com/drive/folders/YOUR_FOLDER_ID" \
  --client-user-id "YOUR_CLIENT_USER_ID" \
  --language "es" \
  --limit 5
```

### Via Crew Handler
```python
from crews.book_ingestion_crew.book_ingestion_crew_handler import BookIngestionCrewHandler

handler = BookIngestionCrewHandler()
result = await handler.execute({
    "google_drive_folder_path": "https://drive.google.com/drive/folders/YOUR_FOLDER_ID",
    "client_user_id": "3a411a30-1653-4caf-acee-de257ff50e36",
    "actor_type": "synth",
    "actor_id": "e30fc9f3-57da-4cf0-84e7-ea9188dd5fba",
    "book_title": "Manuscript Title",
    "book_author": "Author Name",
    "language": "es",
    "process_pages_limit": 5  # Optional: limit pages for testing
})
```

### Test Script
```bash
# Run the 5-file test
python test_book_ingestion_5files.py
```

## Configuration

### Environment Variables
```bash
OPENAI_API_KEY=your-openai-api-key
DATABASE_URL_DIRECT=postgresql://user:pass@host/db
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json  # Optional
```

### Input Schema
```json
{
  "job_key": "book_ingestion_crew",
  "google_drive_folder_path": "string (Google Drive folder URL)",
  "client_user_id": "string (UUID)",
  "actor_type": "string",
  "actor_id": "string (UUID)",
  "book_title": "string",
  "book_author": "string",
  "language": "string (ISO code, default: 'es')",
  "process_pages_limit": "integer (optional, for testing)"
}
```

## Tools Used

1. **GoogleDriveTool**: Lists files in Google Drive folders
2. **GoogleDriveDownloadTool**: Downloads individual files
3. **ImageViewerTool**: Performs 3-pass OCR using GPT-4o
4. **SyncDBStorageTool**: Stores transcriptions in database

## Database Schema

The crew stores data in the `BookIngestions` table:
- `id`: UUID primary key
- `book_key`: Google Drive folder URL
- `page_number`: Extracted from filename
- `file_name`: Original filename
- `language_code`: Language of the text
- `version`: Processing version (default: "original")
- `page_text`: OCR transcription result
- `ocr_metadata`: JSON metadata including file_id and stats
- `created_at`: Timestamp
- `updated_at`: Timestamp

## Recent Updates

### July 2025
- Fixed hanging issue with Google Drive downloads (now sequential)
- Consolidated multiple crew versions into single implementation
- Restored YAML-based configuration
- Fixed database column naming (ClientUsers.clients_id)
- Improved OCR to capture top lines of pages

## Troubleshooting

### Common Issues

1. **Crew Hangs**: Ensure files are downloaded sequentially, not in batch
2. **Missing Top Lines**: OCR prompts now explicitly request first 4-5 lines
3. **Import Errors**: Install sparkjar-shared: `pip install -e ../sparkjar-shared`
4. **Model Errors**: Use gpt-4o-mini for agents, gpt-4o for OCR only

### Performance Tips
- Process 5-10 pages at a time for testing
- Monitor LLM usage (4 calls per page maximum)
- Check logs for detailed progress information

## Future Improvements
- Add retry logic for failed pages
- Implement parallel processing with rate limiting
- Add quality validation for OCR results
- Create export functionality for transcribed books