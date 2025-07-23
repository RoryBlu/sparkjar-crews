# Book Ingestion Crew V2 Implementation Tasks

## Overview
Task list for implementing the enhanced book ingestion crew with multi-pass OCR using ImageViewerTool, page-by-page processing, and multi-tenant database storage.

**Critical Constraint**: Agents CANNOT view images directly - all image operations MUST use ImageViewerTool.

## Task Categories
- 🗄️ Database Setup
- 🔧 Tool Development  
- 🤖 Agent Configuration
- 📝 Task Configuration
- 🧪 Testing & Validation
- 📚 Documentation
- 🚀 Deployment

---

## Phase 1: Database Setup (Priority: HIGH)

### Task 1.1: Store Client Database URL ✅ COMPLETED
**Status**: Vervelyn database URL already inserted by user
- client_id: `1d1c2154-242b-4f49-9ca8-e57129ddc823`
- secret_key: `database_url`
- secret_value: `postgresql://postgres.xkwzjvmckmgfbpxvqrpn:K6kTX6jGjGi1Nw6W@aws-0-us-east-1.pooler.supabase.com:5432/postgres`

### Task 1.2: [ ] Create Database Tables in Vervelyn Database
**Details**:
- Connect to Vervelyn's Supabase instance using stored secret
- Create `book_ingestions` table with proper structure:
  - id: UUID PRIMARY KEY DEFAULT gen_random_uuid()
  - book_key: TEXT NOT NULL (from Google Drive folder name)
  - page_number: INTEGER NOT NULL (extracted from filename)
  - file_name: TEXT NOT NULL (original image filename)
  - language_code: TEXT NOT NULL (ISO code: es, en, fr, etc)
  - version: TEXT NOT NULL DEFAULT 'original'
  - page_text: TEXT NOT NULL (final transcribed text)
  - ocr_metadata: JSONB (confidence scores, passes used, etc)
  - created_at: TIMESTAMP WITH TIME ZONE DEFAULT NOW()
  - updated_at: TIMESTAMP WITH TIME ZONE DEFAULT NOW()
- Create unique constraint on (book_key, page_number, version)
- Add indexes on book_key, language_code, version for performance
- Create `object_embeddings` table with pgvector extension:
  - id: UUID PRIMARY KEY DEFAULT gen_random_uuid()
  - source_id: UUID REFERENCES book_ingestions(id) ON DELETE CASCADE
  - embedding: vector(1536) (OpenAI text-embedding-3-small dimension)
  - chunk_index: INTEGER NOT NULL (order within page)
  - chunk_text: TEXT NOT NULL (512 chars with 128 overlap)
  - start_char: INTEGER NOT NULL
  - end_char: INTEGER NOT NULL
  - embeddings_metadata: JSONB NOT NULL (standard schema)
  - created_at: TIMESTAMP WITH TIME ZONE DEFAULT NOW()
- Add vector similarity index for search performance
- Test table creation with sample insert/select

### Task 1.3: Seed Object Schema in Main Database ✅ COMPLETED
**Details**:
- Connect to main SparkJAR database (not Vervelyn's)
- Insert schema into `object_schemas` table
- Schema name MUST be: `book_ingestion_crew` (exact match to job_key)
- Schema must include all fields from request:
  - job_key: string, required
  - client_user_id: string, required, format: uuid
  - actor_type: string, required, enum: [human, synth]
  - actor_id: string, required, format: uuid
  - google_drive_folder_path: string, required
  - language: string, required, enum: [en, es, fr, de, it]
  - output_format: string, optional, enum: [txt, md, json], default: txt
  - confidence_threshold: number, optional, min: 0, max: 1, default: 0.85
  - book_metadata: object, optional, properties:
    - title: string
    - author: string
    - description: string
    - year: integer
- Verify schema is valid JSON Schema Draft 7
- Test validation with sample request data

---

## Phase 2: Tool Development (Priority: HIGH)

### Task 2.1: [ ] Verify ImageViewerTool Implementation
**Details**:
- Check existing `image_viewer_tool.py` implementation
- Verify it uses GPT-4o model (not gpt-4.1 series)
- Ensure it accepts these parameters:
  - image_path: str (local file path)
  - prompt: str (analysis instructions)
  - context: dict (optional, for multi-pass)
- Verify it returns structured JSON responses
- Test with sample manuscript image:
  - Load test image from Google Drive
  - Send OCR prompt requesting JSON output
  - Verify response includes transcription, confidence, unclear sections
- Check error handling for:
  - Invalid image paths
  - Corrupt image files
  - API timeouts
  - Rate limiting
- Ensure proper base64 encoding for images
- Verify temperature is set low (0.1) for accuracy

### Task 2.2: [ ] Implement DatabaseStorageTool
**File**: `services/crew-api/src/tools/database_storage_tool.py`
**Details**:
- Create new tool extending BaseTool
- Constructor must accept `client_user_id` parameter
- Implement `_init_database()` method:
  - Query main database for ClientUsers table
  - Find record where id = client_user_id
  - Extract clients_id from the record
  - Query ClientSecrets table for client_id + secret_key='database_url'
  - Store database URL for use in _run method
  - Handle missing user or secret gracefully
- Implement `_run()` method accepting:
  - book_key: str (from Google Drive folder)
  - page_number: int
  - file_name: str
  - page_text: str (final transcription)
  - language_code: str
  - version: str (default: 'original')
  - ocr_metadata: dict (all OCR process data)
- Implement `_store_page()` helper:
  - Insert into book_ingestions table
  - Use proper UUID generation
  - Set timestamps appropriately
  - Return the new page_id
- Implement `_generate_embeddings()` helper:
  - Split text into 512-char chunks
  - Create 128-char overlaps between chunks
  - Extend chunks to word boundaries
  - Generate embeddings using OpenAI text-embedding-3-small
  - Store each embedding with full metadata
  - Update total_chunks after processing
- Add transaction support with rollback on error
- Include comprehensive logging at each step
- Return success status with page_id and embedding_count

### Task 2.3: [ ] Verify Sequential Thinking Tool Integration
**Details**:
- Check `sj_sequential_thinking_tool.py` exists and works
- Verify it's properly registered in tool registry
- Check if schema exists in object_schemas table
- Test creating a thinking session:
  - client_user_id: `3a411a30-1653-4caf-acee-de257ff50e36`
  - actor_type: `synth`
  - actor_id: `e30fc9f3-57da-4cf0-84e7-ea9188dd5fba`
  - session_name: "Test OCR Reasoning Session"
  - problem_statement: "Decipher unclear manuscript text"
- Test adding thoughts to the session
- Test searching previous thoughts
- Verify session can be closed properly
- Ensure it integrates with memory service correctly

---

## Phase 3: Agent Configuration (Priority: MEDIUM)

**IMPORTANT**: Agents CANNOT view images directly. All vision work happens inside ImageViewerTool. Agents are orchestrators who USE tools, not vision models themselves.

### Task 3.1: [ ] Create agents_enhanced.yaml
**File**: `services/crew-api/src/crews/book_ingestion_crew/config/agents_enhanced.yaml`
**Details**:
- Define File Manager Agent:
  ```yaml
  file_manager:
    role: Google Drive Operations Specialist
    goal: Efficiently manage file operations from Google Drive
    backstory: Expert in Google Drive API with focus on image file handling
    model: gpt-4.1-mini
    verbose: true
  ```
- Define Vision Specialist Agent:
  ```yaml
  vision_specialist:
    role: ImageViewerTool Orchestrator
    goal: Coordinate multi-pass OCR using ImageViewerTool effectively
    backstory: Expert at crafting prompts and managing ImageViewerTool for accurate transcription
    model: gpt-4.1
    verbose: true
  ```
- Define Reasoning Specialist Agent:
  ```yaml
  reasoning_specialist:
    role: OCR Problem Solver
    goal: Use sequential thinking and targeted ImageViewerTool prompts to resolve uncertainties
    backstory: Expert at breaking down complex OCR problems and using tools strategically
    model: gpt-4.1
    verbose: true
  ```
- Define Data Specialist Agent:
  ```yaml
  data_specialist:
    role: Database Storage Expert
    goal: Reliably store transcribed pages with searchable embeddings
    backstory: Ensures data integrity and searchability for all transcribed content
    model: gpt-4.1-mini
    verbose: true
  ```
- Define Project Manager Agent:
  ```yaml
  project_manager:
    role: Book Processing Coordinator
    goal: Track progress and compile comprehensive results
    backstory: Ensures all pages are processed successfully and reports outcomes
    model: gpt-4.1-mini
    verbose: true
  ```

### Task 3.2: [ ] Update crew.py for Tool Assignment
**Details**:
- Import all required tools at top of file:
  - GoogleDriveTool
  - ImageViewerTool (CRITICAL - agents use this for images)
  - SJSequentialThinkingTool  
  - DatabaseStorageTool (newly created)
- Update `build_crew()` function to assign tools:
  - file_manager: [google_drive]
  - vision_specialist: [image_viewer] ONLY
  - reasoning_specialist: [thinking_tool, image_viewer]
  - data_specialist: [storage_tool]
  - project_manager: [] (no tools needed)
- Ensure DatabaseStorageTool receives client_user_id
- Add clear comment: "Agents CANNOT view images directly"
- Keep simple error handling - just ValueError for missing client_user_id
- Do NOT add custom orchestration logic
- Test tool initialization with sample client_user_id

---

## Phase 4: Task Configuration (Priority: MEDIUM)

### Task 4.1: [ ] Create tasks_enhanced.yaml
**File**: `services/crew-api/src/crews/book_ingestion_crew/config/tasks_enhanced.yaml`
**Details for each task**:

#### list_book_files:
- Description must instruct use of google_drive tool
- Must extract page numbers from batch-based filenames:
  - Files come in batches of 25 pages
  - First number indicates batch start
  - Second number (0-24) indicates position within batch
  - Example: "batch_100_page_0.jpg" = page 100, "batch_100_page_24.jpg" = page 124
  - Formula: page_number = batch_start + position_in_batch
- Sort by calculated page number, not alphabetically
- Return JSON array with: file_id, file_name, calculated_page_number, mime_type
- IMPORTANT: Will need specific prompt instructions for page calculation logic

#### ocr_initial_pass:
- Description MUST specify using image_viewer tool
- Include the EXACT prompt for ImageViewerTool in the description
- The prompt is what does the actual OCR work - agent just passes it
- Pass book metadata as context (title, author, time period, location)
- Request specific JSON structure in response
- Set expected_output to match JSON schema
- Remember: The ImageViewerTool does ALL the vision work, not the agent

#### ocr_refinement_pass:
- Only execute if initial pass confidence < threshold
- Pass previous transcription as context to ImageViewerTool
- Focus prompt on specific unclear sections
- Include previous page ending for context continuity
- Track what changes were made

#### ocr_reasoning_pass:
- Only execute if refinement still has unclear sections
- Use BOTH sequential thinking AND ImageViewerTool
- Sequential thinking helps PLAN what prompts to send to ImageViewerTool
- ImageViewerTool does the actual vision work with targeted prompts
- Document the reasoning process in thinking session
- The agent orchestrates tools, it doesn't "see" or "reason about" images directly

#### store_page_to_database:
- Use database_storage tool with all parameters
- Include full OCR metadata in storage
- Ensure version field is set appropriately
- Handle both successful and failed storage

#### compile_book_results:
- Aggregate all processing outcomes
- Calculate statistics: total pages, success rate, avg confidence
- List any failed pages with reasons
- Provide actionable recommendations

### Task 4.2: [ ] Implement Page Iteration Logic in Tasks
**Details**:
- Research how CrewAI handles iteration over lists
- Design task flow to process pages sequentially (not parallel)
- Ensure each page's context is available to the next
- Implement "previous_page_context" passing between tasks
- Add progress tracking within task descriptions
- Test with 3-page sample to verify sequential processing
- Ensure CrewAI's built-in error handling preserves page order

---

## Phase 5: Testing & Validation (Priority: HIGH)

### Task 5.1: [ ] Create Test Script
**File**: `services/crew-api/scripts/test_book_ingestion_v2.py`
**Test Data** (provided by user):
```python
test_inputs = {
    "job_key": "book_ingestion_crew",
    "client_user_id": "3a411a30-1653-4caf-acee-de257ff50e36",
    "actor_type": "synth",
    "actor_id": "e30fc9f3-57da-4cf0-84e7-ea9188dd5fba",
    "google_drive_folder_path": "sparkjar/vervelyn/castor gonzalez/book 1/",
    "language": "es",
    "output_format": "txt",
    "confidence_threshold": 0.85,
    "book_metadata": {
        "title": "Castor Gonzalez Book 1",
        "author": "Castor Gonzalez",
        "description": "First book manuscript",
        "year": 2024
    }
}
```
**Script Requirements**:
- Import crew kickoff function
- Create proper logging setup
- Execute crew with test inputs
- Capture and display results
- Verify database records were created
- Check embedding generation
- Report timing and performance metrics

### Task 5.2: [ ] Integration Testing Suite
**Test Scenarios**:
- **ImageViewerTool Tests**:
  - Test with clear Spanish manuscript page
  - Test with partially illegible page
  - Test with mixed handwriting styles
  - Verify JSON response structure
  - Check confidence score accuracy
- **Multi-Pass Logic Tests**:
  - Page with 100% confidence (1 pass only)
  - Page with 80% confidence (2 passes)
  - Page with complex uncertainties (3 passes)
  - Verify context passing between passes
- **Database Storage Tests**:
  - Verify client resolution from client_user_id
  - Check page storage with all fields
  - Verify embedding dimensions (1536)
  - Test chunk overlap correctness
  - Verify transaction rollback on error
- **Sequential Processing Tests**:
  - Process 5 pages in order
  - Verify page numbers maintained
  - Check context flows between pages
  - Test with missing page number

### Task 5.3: [ ] Performance and Load Testing
**Metrics to Measure**:
- Time per page (target: <30 seconds)
- Memory usage per page
- Database connection pooling efficiency
- API rate limit management
- Concurrent page processing limits
**Test Scenarios**:
- 10 pages sequential processing
- 50 pages with monitoring
- 100 pages full book test
- Memory leak detection
- Database connection limits
- Error recovery scenarios

---

## Phase 6: Documentation (Priority: MEDIUM)

### Task 6.1: [ ] Update Crew README
**File**: `services/crew-api/src/crews/book_ingestion_crew/README.md`
**Content to Include**:
- Overview of multi-pass OCR approach
- ImageViewerTool requirement explanation
- Database configuration steps
- Example usage with all parameters
- Expected performance metrics
- Troubleshooting common issues
- Sample output structure

### Task 6.2: [ ] Create Deployment Guide
**File**: `services/crew-api/docs/BOOK_INGESTION_DEPLOYMENT.md`
**Sections Required**:
- Prerequisites checklist
- Environment variables (main service only)
- Client secret configuration steps
- Database table creation process
- Railway deployment process
- Health check verification
- Monitoring setup
- Rollback procedures
- Common issues and solutions

---

## Phase 7: Deployment (Priority: LOW)

### Task 7.1: [ ] Pre-Deployment Checklist
**Verify**:
- All dependencies in requirements.txt:
  - crewai>=0.1.0
  - openai>=1.0.0
  - psycopg2-binary>=2.9.0
  - sqlalchemy>=2.0.0
  - pgvector>=0.1.0
- Import paths are correct for Railway
- IPv6 compatibility (bind to 0.0.0.0)
- Memory service URL uses .railway.internal
- All tools are registered properly
- Database migrations are ready

### Task 7.2: [ ] Production Deployment
**Steps**:
- Create git tag for release: v2.0.0-book-ingestion
- Push all changes to GitHub main branch
- Monitor Railway build logs
- Verify deployment successful
- Run smoke test with 1 page
- Check all health endpoints
- Monitor logs for first hour
- Document any issues found
- Create rollback plan if needed

---

## Implementation Priority Order

1. **Complete Database Setup First** (Task 1.2-1.3)
   - Cannot test anything without tables and schema
   
2. **Verify/Build Tools** (Task 2.1-2.3)
   - ImageViewerTool is critical path
   - DatabaseStorageTool needed for storage
   
3. **Configure Agents and Tasks** (Task 3.1-4.2)
   - Define the workflow structure
   - Implement page iteration logic
   
4. **Test with Small Dataset** (Task 5.1)
   - Validate basic functionality
   - Identify issues early
   
5. **Full Integration Testing** (Task 5.2-5.3)
   - Ensure reliability at scale
   - Performance optimization
   
6. **Documentation** (Task 6.1-6.2)
   - Critical for maintenance
   - Required for deployment
   
7. **Deploy to Production** (Task 7.1-7.2)
   - Final validation
   - Monitor closely

---

## Success Criteria

- ✅ 100% OCR accuracy on test manuscript (using multi-pass)
- ✅ All pages stored in correct sequential order
- ✅ Embeddings enable semantic search across book
- ✅ No hardcoded client configurations
- ✅ Process completes without manual intervention
- ✅ Average processing time < 30s per page
- ✅ All tests pass with real data
- ✅ Zero data loss during processing

---

## Risk Mitigation

**Risk**: ImageViewerTool may not return consistent JSON
- **Mitigation**: Add response validation and retry logic in task

**Risk**: Database connections may timeout on long books  
- **Mitigation**: Implement connection pooling and health checks

**Risk**: Memory issues with 600+ page books
- **Mitigation**: Process one page at a time, clean up after each

**Risk**: Sequential thinking may take too long
- **Mitigation**: Set time limits, fall back to best guess

---

**Document Status**: READY FOR IMPLEMENTATION
**Created**: 2025-01-20
**Senior Dev Validation**: Required before starting
**Estimated Timeline**: 3-4 days with disciplined execution