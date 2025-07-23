# Book Ingestion Crew - Requirements Specification

## 1. Purpose
Create a production-ready book ingestion crew that processes handwritten manuscript images from Google Drive, performs OCR, and stores the transcribed text in a PostgreSQL database.

## 2. Core Requirements

### 2.1 Functional Requirements
- **Input**: Google Drive folder URL containing manuscript page images
- **Processing**: 
  - Download files one at a time (not batch)
  - OCR each image using GPT-4o (3 passes for accuracy)
  - Store transcribed text in database
- **Output**: Transcribed pages stored in BookIngestions table
- **Languages**: Support multiple languages (specified in input)
- **File Types**: Support all image formats (PNG, JPG, JPEG, WEBP, GIF, BMP, TIFF)

### 2.2 KISS Principle (MANDATORY)
- Get list of files from Google Drive
- For each file:
  1. Download it
  2. OCR it (3 passes)
  3. Save to database
  4. Move to next file
- NO additional complexity

### 2.3 Performance Requirements
- Process pages sequentially (one at a time)
- Maximum 4 LLM calls per page:
  - 1 agent coordination call
  - 3 OCR passes (all in the tool)
- Must capture top 4-5 lines of each page (current issue)

## 3. Technical Architecture

### 3.1 CrewAI Standards (MUST FOLLOW)
```yaml
# agents.yaml structure
coordinator:
  role: "Book Ingestion Coordinator"
  goal: "Process manuscript pages from Google Drive"
  model: "gpt-4o-mini"  # Standard model
  tools:
    - google_drive_tool
    - image_viewer_tool
    - db_storage_tool

# tasks.yaml structure  
process_pages:
  description: "Process each manuscript page"
  expected_output: "Status of processed pages"
  agent: coordinator
```

### 3.2 Input Schema
```json
{
  "job_key": "book_ingestion_crew",
  "google_drive_folder_path": "string (URL)",
  "client_user_id": "string (UUID)",
  "actor_type": "string",
  "actor_id": "string (UUID)",
  "book_title": "string",
  "book_author": "string",
  "language": "string (ISO code, default: 'es')",
  "process_pages_limit": "integer (optional)"
}
```

### 3.3 Database Schema (BookIngestions)
- book_key: Google Drive folder URL
- page_number: Extracted from filename
- file_name: Original filename (key identifier)
- language_code: From input
- version: "original"
- page_text: OCR result
- ocr_metadata: JSON with file_id and stats

### 3.4 Tools Required
1. **GoogleDriveTool**: List files (NO download in listing)
2. **GoogleDriveDownloadTool**: Download one file at a time
3. **ImageViewerTool**: 3-pass OCR with GPT-4o
4. **DBStorageTool**: Simple synchronous database storage

## 4. Implementation Standards

### 4.1 File Structure
```
crews/book_ingestion_crew/
├── __init__.py
├── crew.py              # CrewAI crew definition
├── config/
│   ├── agents.yaml     # Agent definitions
│   └── tasks.yaml      # Task definitions
└── utils.py            # Utility functions
```

### 4.2 Code Standards
- Use CrewAI's `kickoff_for_each` for page processing
- YAML-based configuration (no hardcoded agents)
- Standard OpenAI models only
- Proper error handling and logging
- Schema validation for inputs

### 4.3 What NOT to Do
- ❌ NO custom process loops
- ❌ NO non-standard model names
- ❌ NO async complexity in tools
- ❌ NO multiple tool versions
- ❌ NO feature creep beyond requirements

## 5. Testing Requirements
- Test with 5 manuscript pages
- Verify all pages stored correctly
- Check OCR captures top lines
- Validate 4 LLM calls per page limit
- All tests must pass

## 6. Success Criteria
1. Follows CrewAI standards with YAML configs
2. Successfully processes 5 test pages
3. Stores all transcriptions in database
4. Uses only 4 LLM calls per page
5. Captures complete page content including top lines
6. Simple, maintainable code following KISS principle

## 7. Current Blockers
1. Abandoned YAML configuration needs restoration
2. Non-existent model usage needs correction
3. Storage tool async/sync issues need simplification
4. Missing schema validation
5. Complex manual orchestration needs removal