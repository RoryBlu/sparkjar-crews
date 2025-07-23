#!/usr/bin/env python
"""
Test script for the manual loop processing orchestrator.
"""

import sys
import os
import logging
from unittest.mock import Mock, patch, MagicMock
import json

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the crew module
from crews.book_ingestion_crew.crew import manual_loop_orchestrator, get_files_from_drive

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_manual_loop_orchestrator():
    """Test the manual loop orchestrator with mocked tools."""
    
    # Mock input data
    test_inputs = {
        "client_user_id": "test-client-123",
        "google_drive_folder_path": "test/folder/path",
        "language": "en",
        "process_pages_limit": 2  # Limit to 2 pages for testing
    }
    
    # Mock file data that would come from Google Drive
    mock_files = [
        {
            "file_id": "file1",
            "name": "baron001.png",
            "file_name": "baron001.png",
            "mime_type": "image/png"
        },
        {
            "file_id": "file2", 
            "name": "baron001 1.png",
            "file_name": "baron001 1.png",
            "mime_type": "image/png"
        }
    ]
    
    # Mock the get_files_from_drive function
    with patch('crews.book_ingestion_crew.crew.get_files_from_drive') as mock_get_files:
        mock_get_files.return_value = mock_files
        
        # Mock the tools
        with patch('crews.book_ingestion_crew.crew.GoogleDriveDownloadTool') as mock_download_tool_class, \
             patch('crews.book_ingestion_crew.crew.ImageViewerTool') as mock_ocr_tool_class, \
             patch('crews.book_ingestion_crew.crew.SyncDBStorageTool') as mock_storage_tool_class:
            
            # Create mock tool instances
            mock_download_tool = Mock()
            mock_ocr_tool = Mock()
            mock_storage_tool = Mock()
            
            mock_download_tool_class.return_value = mock_download_tool
            mock_ocr_tool_class.return_value = mock_ocr_tool
            mock_storage_tool_class.return_value = mock_storage_tool
            
            # Mock tool responses
            mock_download_tool._run.return_value = json.dumps({
                "status": "success",
                "local_path": "/tmp/test_image.png"
            })
            
            mock_ocr_tool._run.return_value = json.dumps({
                "status": "success",
                "transcription": "Test transcribed text",
                "processing_stats": {
                    "total_words": 10,
                    "normal_transcription": 8,
                    "context_logic_transcription": 2,
                    "unable_to_transcribe": 0
                },
                "unclear_sections": []
            })
            
            mock_storage_tool._run.return_value = json.dumps({
                "status": "success",
                "page_id": "page-123"
            })
            
            # Create a simple logger mock
            simple_logger = Mock()
            
            # Run the orchestrator
            logger.info("Testing manual loop orchestrator...")
            result = manual_loop_orchestrator(test_inputs, simple_logger)
            
            # Verify results
            logger.info(f"Result: {result}")
            
            # Assertions
            assert result["status"] == "completed"
            assert result["total_pages"] == 2
            assert result["processed_successfully"] == 2
            assert result["failed"] == 0
            assert len(result["successful_pages"]) == 2
            assert len(result["failed_pages"]) == 0
            
            # Verify tool calls
            assert mock_download_tool._run.call_count == 2
            assert mock_ocr_tool._run.call_count == 2
            assert mock_storage_tool._run.call_count == 2
            
            # Verify file processing order
            successful_pages = result["successful_pages"]
            assert successful_pages[0]["page_number"] == 1  # baron001.png
            assert successful_pages[1]["page_number"] == 2  # baron001 1.png
            
            logger.info("✅ Manual loop orchestrator test passed!")
            return True

def test_error_handling():
    """Test error handling in the orchestrator."""
    
    test_inputs = {
        "client_user_id": "test-client-123",
        "google_drive_folder_path": "test/folder/path",
        "language": "en"
    }
    
    mock_files = [
        {
            "file_id": "file1",
            "name": "baron001.png",
            "file_name": "baron001.png",
            "mime_type": "image/png"
        }
    ]
    
    with patch('crews.book_ingestion_crew.crew.get_files_from_drive') as mock_get_files:
        mock_get_files.return_value = mock_files
        
        with patch('crews.book_ingestion_crew.crew.GoogleDriveDownloadTool') as mock_download_tool_class:
            mock_download_tool = Mock()
            mock_download_tool_class.return_value = mock_download_tool
            
            # Mock download failure
            mock_download_tool._run.return_value = json.dumps({
                "status": "error",
                "error": "Download failed"
            })
            
            # Run the orchestrator
            logger.info("Testing error handling...")
            result = manual_loop_orchestrator(test_inputs)
            
            # Verify error handling
            assert result["status"] == "completed"
            assert result["total_pages"] == 1
            assert result["processed_successfully"] == 0
            assert result["failed"] == 1
            assert len(result["failed_pages"]) == 1
            assert "Download failed" in result["failed_pages"][0]["error"]
            
            logger.info("✅ Error handling test passed!")
            return True

if __name__ == "__main__":
    try:
        logger.info("Starting manual loop orchestrator tests...")
        
        # Run tests
        test_manual_loop_orchestrator()
        test_error_handling()
        
        logger.info("🎉 All tests passed!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)