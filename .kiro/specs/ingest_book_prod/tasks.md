# Implementation Plan

- [ ] 1. Create YAML configuration files for CrewAI agents and tasks
  - Create agents.yaml with minimal agent definitions using gpt-4.1-nano model
  - Create tasks.yaml with concise task descriptions to minimize LLM calls
  - Ensure single-pass processing configuration
  - _Requirements: 3.1, 3.2, 3.3_

- [ ] 2. Implement GoogleDriveDownloadTool for individual file downloads
  - Create tool class that downloads one file at a time from Google Drive
  - Implement client credential retrieval from database
  - Add support for all required image formats (PNG, JPG, JPEG, WEBP, GIF, BMP, TIFF)
  - Include proper error handling and temporary file management
  - _Requirements: 1.1, 1.2, 1.3_

- [ ] 3. Update ImageViewerTool to ensure complete page capture
  - Modify OCR prompts to explicitly capture top 4-5 lines of each page
  - Implement exactly 3 OCR passes using GPT-4o vision model
  - Add comprehensive error handling for unclear handwriting sections
  - Return structured JSON with transcription and processing statistics
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [ ] 4. Implement SyncDBStorageTool for reliable database operations
  - Create synchronous database storage tool using SQLAlchemy
  - Implement BookIngestions table schema compliance
  - Add proper error handling and transaction management
  - Include page number extraction from filename logic
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [ ] 5. Create input validation schema and error handling
  - Implement Pydantic schema for input validation
  - Add comprehensive error messages for missing required fields
  - Validate language codes against supported languages
  - Handle optional process_pages_limit parameter
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [ ] 6. Implement manual loop processing orchestrator
  - Create main crew orchestration function using manual loops instead of kickoff_for_each
  - Implement sequential file processing (one page at a time)
  - Add file discovery and sorting logic using GoogleDriveTool
  - Ensure maximum 4 LLM calls per page (1 coordination + 3 OCR)
  - _Requirements: 6.1, 6.2, 6.3, 2.3_

- [ ] 7. Build crew factory with YAML-based configuration
  - Create crew builder function that loads agents and tasks from YAML files
  - Implement proper agent initialization with gpt-4.1-nano model
  - Configure sequential processing pipeline
  - Add tool assignment to appropriate agents
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [ ] 8. Implement comprehensive error handling and logging
  - Add error handling for individual page failures without stopping entire process
  - Implement proper logging with context (page number, file name)
  - Add retry logic for transient failures
  - Create graceful degradation for OCR quality issues
  - _Requirements: 6.4, 2.4_

- [ ] 9. Create file sorting and page number extraction utilities
  - Implement filename parsing to extract page numbers
  - Create file sorting logic to process pages in correct order
  - Add support for various filename formats
  - Handle edge cases in filename parsing
  - _Requirements: 5.3, 6.1_

- [ ] 10. Write comprehensive unit tests for all components
  - Create unit tests for each tool (GoogleDriveDownloadTool, ImageViewerTool, SyncDBStorageTool)
  - Test input validation schema with various input scenarios
  - Test error handling paths and edge cases
  - Mock external dependencies (Google Drive API, database)
  - _Requirements: All requirements validation_

- [ ] 11. Implement integration tests with test data
  - Create end-to-end test with 5 manuscript page images
  - Test complete workflow from Google Drive to database storage
  - Validate OCR accuracy and top-line capture
  - Verify LLM call count limits (max 4 per page)
  - _Requirements: 2.2, 2.3, 1.4_

- [ ] 12. Add performance monitoring and metrics collection
  - Implement processing time measurement per page
  - Add LLM call counting and validation
  - Create memory usage monitoring during image processing
  - Add database transaction performance tracking
  - _Requirements: 2.3, 6.1, 6.2_

- [ ] 13. Create main entry point and crew handler integration
  - Implement main kickoff function that orchestrates the entire process
  - Add proper result compilation and status reporting
  - Integrate with existing crew handler infrastructure
  - Ensure compatibility with crew registry system
  - _Requirements: 1.4, 5.1, 6.3_

- [ ] 14. Implement cleanup and resource management
  - Add temporary file cleanup after processing each page
  - Implement proper database connection management
  - Add Google Drive API credential caching per client
  - Create memory management for large image files
  - _Requirements: 1.2, 5.1, 6.2_

- [ ] 15. Final integration and production readiness testing
  - Test complete system with real Google Drive folder and credentials
  - Validate all requirements are met through comprehensive testing
  - Perform load testing with multiple pages
  - Verify KISS principle compliance and code maintainability
  - _Requirements: All requirements final validation_