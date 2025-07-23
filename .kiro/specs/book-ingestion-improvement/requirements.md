# Book Ingestion Crew Improvement Requirements

## Project: Vervelyn Publishing Book Ingestion System
**Date**: 2025-01-20  
**Client**: Vervelyn Publishing  
**Scope**: Improve OCR accuracy and implement page-by-page processing with database storage

## 1. Executive Summary

The current book ingestion crew is experiencing issues with OCR accuracy and page ordering. This specification outlines improvements to implement a multi-pass GPT-4o vision approach, page-by-page processing with todo tracking, and direct database storage for Vervelyn Publishing.

## 2. Current State Analysis

### 2.1 Existing Functionality
- Single-pass OCR using GPT-4o
- Batch processing of all images at once
- Results saved to Google Drive as a single text file
- Spanish manuscript focus with hardcoded prompts
- No persistent storage of individual pages

### 2.2 Identified Issues
1. **Accuracy**: Single-pass OCR misses context and produces errors
2. **Page Ordering**: Pages get mixed up during batch processing
3. **No Persistence**: Results only saved to Google Drive, not queryable
4. **Memory Issues**: Processing 660 files at once causes problems
5. **Language Hardcoding**: System hardcoded for Spanish only

## 3. Functional Requirements

### 3.1 Multi-Pass OCR Strategy
**Requirement ID**: FR-001  
**Priority**: HIGH  
**Description**: Implement 2-3 pass OCR using GPT-4o vision model

#### Pass 1: Initial OCR
- Vision Specialist agent uses ImageViewerTool with GPT-4o
- Tool performs initial transcription and returns structured data
- Capture confidence levels and unclear sections
- Return structured result with transcription and metadata

#### Pass 2: Context-Aware Refinement  
- Vision Specialist uses ImageViewerTool again with enhanced prompts
- Tool receives Pass 1 results as context
- Include prompts for:
  - Storyline context consideration
  - Letter clarity analysis
  - Word size patterns
  - Contextual word relationships
- Focus on unclear sections identified in Pass 1

#### Pass 3: Final Verification (if needed)
- Only triggered if Pass 2 indicates remaining uncertainties
- Reasoning Specialist uses ImageViewerTool with full context
- Tool receives Pass 1 + Pass 2 results
- Final deduction pass with emphasis on logical consistency

### 3.2 Page-by-Page Processing
**Requirement ID**: FR-002  
**Priority**: HIGH  
**Description**: Process files individually with todo tracking

1. **File Listing**: Fetch complete list of image files from Google Drive
2. **Todo Creation**: Create internal todo list with all files
3. **Sequential Processing**: Process one file at a time:
   - Download individual file
   - Apply multi-pass OCR
   - Use sequential thinking tool for complex sections
   - Save to database immediately
   - Mark todo item complete
   - Continue to next file
4. **Progress Tracking**: Maintain progress state for resumability

### 3.3 Request Schema
**Requirement ID**: FR-003  
**Priority**: HIGH  
**Description**: Enhanced request schema with page information

#### Request JSON Schema
```json
{
  "job_key": "book_ingestion_crew",
  "client_user_id": "uuid",         // User within the client organization
  "actor_type": "human|synth",      // Type of actor performing the job
  "actor_id": "uuid",               // ID of the actor (synth or human)
  "google_drive_folder_path": "string",  // e.g., "sparkjar/vervelyn/castor gonzalez/book 1/"
  "language": "en|es|fr|de|it",     // Language for OCR processing
  "output_format": "txt|md|json",   // Output format (default: txt)
  "confidence_threshold": 0.85,     // Minimum OCR confidence (0-1)
  "book_metadata": {                // Optional metadata
    "title": "string",
    "author": "string", 
    "description": "string",
    "year": integer
  }
}
```

Note: `client_id` is resolved from `client_user_id` via database lookup

The crew must extract page numbers from filenames to ensure correct ordering.

### 3.4 Database Integration
**Requirement ID**: FR-004  
**Priority**: HIGH  
**Description**: Store results in Vervelyn Publishing database

#### Database Connection
- PostgreSQL database at client's Supabase instance
- Connection string stored in `client_secrets` table
- Retrieved using `client_user_id` → `clients_id` → `secret_key='database_url'`
- No environment variables for client-specific databases

#### Table Schema: `book_ingestions`
```sql
CREATE TABLE book_ingestions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    book_key TEXT NOT NULL,               -- Google Drive folder name
    page_number INTEGER NOT NULL,         -- Sequential page number
    file_name TEXT NOT NULL,              -- Original image filename
    language_code TEXT NOT NULL,          -- ISO language code (en, es, fr, etc)
    version TEXT NOT NULL,                -- Book version type
    page_text TEXT NOT NULL,              -- Final transcribed text
    ocr_metadata JSONB,                   -- Pass details, confidence, etc
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexes for performance
    UNIQUE(book_key, page_number, version),
    INDEX idx_book_key (book_key),
    INDEX idx_language (language_code),
    INDEX idx_version (version)
);
```

#### Table Schema: `object_embeddings`
```sql
CREATE TABLE object_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL REFERENCES book_ingestions(id) ON DELETE CASCADE,
    embedding vector(1536),               -- OpenAI text-embedding-3-small dimension
    chunk_index INTEGER NOT NULL,         -- Order of chunks within page
    chunk_text TEXT NOT NULL,             -- Text that was embedded
    start_char INTEGER NOT NULL,          -- Starting character position in page
    end_char INTEGER NOT NULL,            -- Ending character position in page
    embeddings_metadata JSONB NOT NULL,   -- Metadata following standard schema
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexes
    INDEX idx_source_id (source_id),
    INDEX idx_embeddings_vector (embedding vector_cosine_ops)
);
```

#### Embeddings Metadata Schema
```json
{
  "book_key": "string",          // Book identifier
  "page_number": "integer",      // Page number
  "language_code": "string",     // ISO language code
  "version": "string",           // Book version
  "chunk_index": "integer",      // Chunk order within page
  "total_chunks": "integer",     // Total chunks for this page
  "overlap_chars": "integer",    // Character overlap with adjacent chunks
  "model": "string",             // Embedding model used
  "dimension": "integer",        // Vector dimension
  "token_count": "integer",      // Tokens in chunk
  "processing_timestamp": "ISO8601"
}
```

#### Version Values (non-exhaustive)
- `original` - Original language manuscript
- `literary_translation` - Literary translation
- `english_translation` - English translation
- `annotated` - Annotated version
- `draft_v1`, `draft_v2` - Draft versions
- Any other version identifier as needed

### 3.5 Configuration Requirements
**Requirement ID**: FR-005  
**Priority**: MEDIUM  
**Description**: Externalize configuration

1. **Database Credentials**: Store in `client_secrets` table with `secret_key='database_url'`
2. **Language Support**: Make language configurable, not hardcoded
3. **Model Selection**: Models specified in agents.yaml (use gpt-4o for vision agent)
4. **Retry Logic**: Configurable retry attempts for API failures

## 4. Non-Functional Requirements

### 4.1 Quality & Reliability
- **NFR-001**: Achieve 100% accuracy through multi-pass reasoning
- **NFR-002**: Save progress after each page completion
- **NFR-003**: Graceful error handling with specific error messages
- **NFR-004**: Implement retry logic for API failures
- **NFR-005**: Support resuming interrupted jobs

### 4.2 Security
- **NFR-006**: Store database credentials as client secrets
- **NFR-007**: Use JWT authentication for API access
- **NFR-008**: No hardcoded credentials in code

## 5. Technical Constraints

1. **GPT-4o Model**: Must use specifically GPT-4o for vision capabilities
2. **Image Formats**: Support JPEG, PNG, WebP formats
3. **Text Length**: Handle pages with 100-1000 words
4. **Database**: Must use provided PostgreSQL instance

## 6. Success Criteria

1. **Accuracy**: 100% transcription accuracy - every readable word correctly transcribed
2. **Completeness**: All pages processed and stored successfully  
3. **Order**: Pages maintain correct sequential order
4. **Quality**: Multi-pass reasoning resolves all ambiguous text
5. **Reliability**: Successful completion without manual intervention

## 7. Audit Findings

### 7.1 Book Ingestion Crew Audit
✅ **Strengths**:
- Clean separation of agents and tasks
- Proper tool integration
- Configuration externalized to YAML

❌ **Issues**:
- Hardcoded Spanish language in prompts
- Batch processing causes memory/ordering issues  
- No database integration
- Single-pass OCR only
- No progress tracking

### 7.2 Sequential Thinking Tool Audit
✅ **Excellent Implementation**:
- Comprehensive session management
- Thought revision tracking
- Search and analysis capabilities
- Clean API design
- Proper error handling

🎯 **Required Use**: Use for complex OCR problem solving - piecing together story context to decipher difficult words

⚠️ **Check Required**: Review object_schemas table for thinking tool integration - verify schema exists and is properly configured

### 7.3 ImageViewerTool Requirements
🔧 **Critical Functionality**:
- Agents CANNOT view images directly - must use ImageViewerTool
- Tool wraps GPT-4o vision capabilities
- Accepts image path and custom prompts
- Returns structured JSON responses
- Supports context from previous passes

✅ **Multi-Pass Support**:
- Pass 1: Basic transcription with confidence tracking
- Pass 2: Context-aware refinement with previous results
- Pass 3: Deep reasoning with all accumulated context

## 8. Dependencies

1. **Google Drive API**: For file access
2. **OpenAI API**: For GPT-4o vision model
3. **PostgreSQL**: For data storage
4. **Supabase**: Database hosting
5. **CrewAI**: Agent orchestration framework

## 9. Open Questions

1. **Page Numbering**: How to determine correct page order from filenames?
2. **Character Encoding**: Special character handling for different languages?
3. **Image Quality**: Minimum resolution requirements?
4. **Partial Failures**: How to handle if some pages fail after retries?
5. **Duplicate Detection**: How to handle re-processing of same book?

## 10. Action Items

### 10.1 Database Setup
1. Store client database URL in `client_secrets` table:
   ```sql
   INSERT INTO client_secrets (client_id, secret_key, secret_value)
   VALUES ('1d1c2154-242b-4f49-9ca8-e57129ddc823', 'database_url', 'postgresql://...');
   ```
2. Create `book_ingestions` and `object_embeddings` tables in client's database
3. Seed object_schemas with book_ingestion_crew schema

### 10.2 Implementation Steps
1. Review and approve requirements
2. Create detailed design document
3. Implement multi-pass OCR logic with GPT-4o
4. Integrate sequential thinking tool for complex passages
5. Add database integration with proper chunking
6. Create embeddings with overlap for semantic search
7. Test with sample manuscript
8. Deploy to production

## 11. Test Configuration

### Test Values for Vervelyn Publishing
- **client_id**: `1d1c2154-242b-4f49-9ca8-e57129ddc823`
- **client_user_id**: `3a411a30-1653-4caf-acee-de257ff50e36`
- **actor_type**: `synth`
- **actor_id**: `e30fc9f3-57da-4cf0-84e7-ea9188dd5fba`
- **google_drive_folder_path**: `sparkjar/vervelyn/castor gonzalez/book 1/`

---

**Document Status**: READY FOR REVIEW  
**Author**: Senior Development Team  
**Review Required By**: Product Owner