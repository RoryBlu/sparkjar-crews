# Requirements Document

## Introduction

This specification defines the requirements for a production-ready book ingestion crew that processes handwritten manuscript images from Google Drive, performs OCR using GPT-4o, and stores the transcribed text in a PostgreSQL database. The system must follow CrewAI standards and the KISS principle for maintainable, reliable operation.

## Requirements

### Requirement 1

**User Story:** As a content manager, I want to process manuscript images from Google Drive, so that I can digitize handwritten books into searchable text format.

#### Acceptance Criteria

1. WHEN a Google Drive folder URL is provided THEN the system SHALL list all image files in the folder
2. WHEN processing begins THEN the system SHALL download files one at a time sequentially
3. WHEN an image is downloaded THEN the system SHALL support PNG, JPG, JPEG, WEBP, GIF, BMP, and TIFF formats
4. WHEN processing completes THEN the system SHALL store transcribed pages in the BookIngestions database table

### Requirement 2

**User Story:** As a quality assurance specialist, I want OCR processing with multiple passes, so that I can ensure accurate text transcription from handwritten manuscripts.

#### Acceptance Criteria

1. WHEN an image is processed THEN the system SHALL perform exactly 3 OCR passes using GPT-4o
2. WHEN OCR processing occurs THEN the system SHALL capture the complete page content including the top 4-5 lines
3. WHEN processing a page THEN the system SHALL use a maximum of 4 LLM calls (1 coordination + 3 OCR passes)
4. WHEN OCR completes THEN the system SHALL store the transcribed text with metadata including file_id and processing stats

### Requirement 3

**User Story:** As a system administrator, I want the crew to follow CrewAI standards, so that I can maintain and deploy the system reliably.

#### Acceptance Criteria

1. WHEN the crew is configured THEN the system SHALL use YAML-based agent and task definitions
2. WHEN agents are defined THEN the system SHALL use only standard OpenAI models (gpt-4.1-mini for coordination)
3. WHEN processing occurs THEN the system SHALL use CrewAI's kickoff_for_each method for page processing
4. WHEN tools are integrated THEN the system SHALL use GoogleDriveTool, GoogleDriveDownloadTool, ImageViewerTool, and DBStorageTool

### Requirement 4

**User Story:** As a developer, I want proper input validation and schema compliance, so that I can ensure data integrity and system reliability.

#### Acceptance Criteria

1. WHEN input is received THEN the system SHALL validate against the defined JSON schema
2. WHEN required fields are missing THEN the system SHALL return appropriate error messages
3. WHEN language is specified THEN the system SHALL support multiple languages with ISO language codes
4. WHEN optional process_pages_limit is provided THEN the system SHALL respect the limit during processing

### Requirement 5

**User Story:** As a database administrator, I want structured data storage, so that I can query and manage transcribed content effectively.

#### Acceptance Criteria

1. WHEN storing transcriptions THEN the system SHALL use the BookIngestions table schema
2. WHEN saving page data THEN the system SHALL include book_key, page_number, file_name, language_code, version, page_text, and ocr_metadata
3. WHEN extracting page numbers THEN the system SHALL derive page_number from the original filename
4. WHEN storing metadata THEN the system SHALL save OCR processing statistics as JSON

### Requirement 6

**User Story:** As a performance monitor, I want efficient sequential processing, so that I can ensure system resources are used optimally.

#### Acceptance Criteria

1. WHEN processing multiple pages THEN the system SHALL process pages sequentially, not in parallel
2. WHEN downloading files THEN the system SHALL download one file at a time, not in batches
3. WHEN processing completes THEN the system SHALL move to the next file only after current file is fully processed
4. WHEN errors occur THEN the system SHALL implement proper error handling and logging without stopping the entire process