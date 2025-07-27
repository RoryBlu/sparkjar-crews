# Implementation Plan

## Overview
Book Translation Crew - a separate, standalone crew that translates previously ingested books using standard CrewAI patterns.

## Phase 1: Core Implementation

- [x] 1. Create crew structure
  - [x] 1.1 Create `src/crews/book_translation_crew/` directory
  - [x] 1.2 Create `__init__.py`, `main.py`, and `crew.py`
  - [x] 1.3 Create `book_translation_crew_handler.py`
    - Implemented BookTranslationCrewHandler class
    - Extended BaseCrewHandler
    - Added execute() method for API integration

- [x] 2. Implement tools
  - [x] 2.1 Create `simple_db_query_tool.py`
    - Handles client database connection via secrets
    - Queries pages from book_ingestions table
    - Returns structured page data
  - [x] 2.2 Create `simple_db_storage_tool.py` (reused existing)
    - Already handles client DB connection
    - Stores to book_ingestions with proper versioning

- [x] 3. Configure agent and tasks
  - [x] 3.1 Create `config/agents.yaml`
    - Single translation_agent with both tools
    - Uses gpt-4.1-mini model
  - [x] 3.2 Create `config/tasks.yaml`
    - Four sequential tasks as per design:
    - query_pages, translate_pages, store_translations, report_results

- [x] 4. Fix implementation issues
  - [x] 4.1 Fix main.py kickoff function
    - Remove all direct database queries
    - Let crew handle everything via tools
    - Simple crew.kickoff() call only
  - [x] 4.2 Update task descriptions
    - Make translate_pages task explicit about complete translation
    - Add batch processing instructions
    - Ensure no summarization happens
  - [x] 4.3 Test tools work correctly
    - Verify simple_db_query_tool connects to client DB
    - Verify simple_db_storage_tool stores translations
    - Check error handling

## Phase 2: Testing & Validation

- [ ] 5. Create test suite
  - [ ] 5.1 Unit tests
    - Test BookTranslationCrewHandler.execute()
    - Test input validation
    - Test error handling
  - [ ] 5.2 Integration test with 5-page sample
    - Create test data in database
    - Run full translation flow
    - Verify complete translations (not summaries)
    - Verify storage with correct version

- [ ] 6. Run full book translation
  - [ ] 6.1 Execute on El Baron's book (635+ pages)
    - Monitor crew_job_events for progress
    - Check for complete translations
    - Verify all pages stored
  - [ ] 6.2 Performance validation
    - Measure total time
    - Calculate API costs
    - Check memory usage

## Phase 3: Production Readiness

- [ ] 7. Error handling & monitoring
  - [ ] 7.1 Verify crew logging
    - All progress logged to crew_job_events
    - No file logging
    - Clear error messages
  - [ ] 7.2 Test error recovery
    - Handle API rate limits
    - Continue on individual page failures
    - Report failures in final summary

- [x] 8. Documentation
  - [x] 8.1 README.md created
  - [x] 8.2 Design document updated
  - [ ] 8.3 Add usage examples
    - How to trigger via API
    - Expected response format
    - Common error scenarios

## Current Status

### Completed
- Crew structure created
- Tools implemented (query and storage)
- Agent and tasks configured
- Basic kickoff function exists

### Needs Fixing
- main.py kickoff doing too much work (should just call crew.kickoff)
- Task descriptions need to be more explicit about complete translation
- Need to verify tools work with client database connection

### Not Started
- Unit tests
- Integration tests
- Full book translation run
- Performance validation

## Next Steps

1. **IMMEDIATE**: Fix main.py to properly use crew instead of doing direct work
2. **THEN**: Update task descriptions to ensure complete translations
3. **FINALLY**: Run 5-page test to validate before full book

## Implementation Guidelines

### DO:
- Follow the design spec exactly
- Use the tools for ALL database operations
- Let the crew handle the workflow
- Log progress to crew_job_events

### DON'T:
- Do direct database queries in kickoff
- Create log files
- Summarize instead of translate
- Add complexity not in the design