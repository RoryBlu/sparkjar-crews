# Requirements Document

## Introduction

The Book Translation feature extends the existing book_ingestion_crew to translate previously ingested content into different languages. This is a simple addition that queries ingested pages, translates them in batches, and stores the results back in the BookIngestions table with appropriate versioning.

## Requirements

### Requirement 1: Source Data Processing

**User Story:** As a content manager, I want to translate ingested book pages from their original language to English, so that I can make the content accessible to English-speaking readers.

#### Acceptance Criteria

1. WHEN a book translation request is submitted THEN the system SHALL retrieve all pages from the BookIngestions table for the specified book_key
2. WHEN retrieving source pages THEN the system SHALL filter by book_key and version='original' to get the source content
3. WHEN source pages are found THEN the system SHALL sort them by page_number for sequential processing
4. WHEN no source pages exist THEN the system SHALL return an error indicating the book has not been ingested

### Requirement 2: Translation Quality

**User Story:** As a quality assurance specialist, I want high-quality contextual translations, so that the target language version accurately conveys the meaning of the original text.

#### Acceptance Criteria

1. WHEN translating text THEN the system SHALL perform contextual translation that preserves meaning (NOT word-for-word)
2. WHEN processing pages THEN the system SHALL batch pages for efficient API usage (e.g., 5-10 pages per request)
3. WHEN translation is complete THEN the system SHALL maintain paragraph structure and formatting from the original
4. WHEN encountering unclear text THEN the system SHALL use context from surrounding pages to improve accuracy

### Requirement 3: Database Storage

**User Story:** As a database administrator, I want translated content stored using existing tools and patterns, so that I can maintain consistency with the current system.

#### Acceptance Criteria

1. WHEN storing translations THEN the system SHALL use the existing sync_db_storage_tool
2. WHEN creating translation records THEN the system SHALL set version='translation_{language_code}' (e.g., 'translation_en')
3. WHEN saving translated pages THEN the system SHALL preserve all original metadata and add translation metadata
4. WHEN handling errors THEN the system SHALL use existing database transaction patterns for consistency

### Requirement 4: Error Handling and Recovery

**User Story:** As a system operator, I want robust error handling during translation, so that individual page failures don't stop the entire translation process.

#### Acceptance Criteria

1. WHEN a page translation fails THEN the system SHALL log the error and continue with the next page
2. WHEN translation quality is low THEN the system SHALL mark the page for manual review in metadata
3. WHEN database storage fails THEN the system SHALL retry the operation with exponential backoff
4. WHEN the process completes THEN the system SHALL provide a summary of successful and failed translations

### Requirement 5: Simple Implementation

**User Story:** As a developer, I want to extend the existing book_ingestion_crew rather than create a new crew, so that we maintain simplicity and reuse existing code.

#### Acceptance Criteria

1. WHEN implementing translation THEN the system SHALL add a new method to the existing book_ingestion_crew
2. WHEN using tools THEN the system SHALL reuse existing database_tool and sync_db_storage_tool
3. WHEN processing translations THEN the system SHALL use a single agent with clear responsibilities
4. WHEN implementing features THEN the system SHALL follow KISS principle and avoid overengineering