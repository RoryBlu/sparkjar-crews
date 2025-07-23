#!/usr/bin/env python
"""
Comprehensive test for the manual loop processing orchestrator.
Tests all requirements and edge cases.
"""

import sys
import os
import logging
from unittest.mock import Mock, patch, MagicMock
import json

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crews.book_ingestion_crew.crew import manual_loop_orchestrator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_requirements_compliance():
    """Test that all requirements are met."""
    
    test_inputs = {
        "client_user_id": "test-client-123",
        "google_drive_folder_path": "test/folder/path",
        "language": "en",
        "process_pages_limit": 2
    }
    
    # Mock files with different page numbers to test sorting
    mock_files = [
        {"file_id": "file2", "name": "baron001 1.png", "file_name": "baron001 1.png", "mime_type": "image/png"},
        {"file_id": "file1", "name": "baron001.png", "file_name": "baron001.png", "mime_type": "image/png"},
    ]
    
    with patch('crews.book_ingestion_crew.crew.get_files_from_drive') as mock_get_files:
        mock_get_files.return_value = mock_files
        
        with patch('crews.book_ingestion_crew.crew.GoogleDriveDownloadTool') as mock_download_tool_class, \
             patch('crews.book_ingestion_crew.crew.ImageViewerTool') as mock_ocr_tool_class, \
             patch('crews.book_ingestion_crew.crew.SyncDBStorageTool') as mock_storage_tool_class:
            
            mock_download_tool = Mock()
            mock_ocr_tool = Mock()
            mock_storage_tool = Mock()
            
            mock_download_tool_class.return_value = mock_download_tool
            mock_ocr_tool_class.return_value = mock_ocr_tool
            mock_storage_tool_class.return_value = mock_storage_tool
            
            # Mock responses
            mock_download_tool._run.return_value = json.dumps({
                "status": "success",
                "local_path": "/tmp/test_image.png"
            })
            
            mock_ocr_tool._run.return_value = json.dumps({
                "status": "success",
                "transcription": "Test transcribed text with top lines captured",
                "processing_stats": {
                    "total_words": 20,
                    "normal_transcription": 15,
                    "context_logic_transcription": 3,
                    "unable_to_transcribe": 2
                },
                "unclear_sections": ["unclear1", "unclear2"],
                "ocr_passes": 3,
                "model_used": "gpt-4o"
            })
            
            mock_storage_tool._run.return_value = json.dumps({
                "status": "success",
                "page_id": "page-123"
            })
            
            # Run orchestrator
            result = manual_loop_orchestrator(test_inputs)
            
            # Test Requirement 6.1: Sequential processing
            assert result["status"] == "completed"
            assert result["processed_successfully"] == 2
            
            # Test Requirement 6.2: One file at a time
            assert mock_download_tool._run.call_count == 2  # Called once per file
            
            # Test Requirement 6.3: File sorting (baron001.png should come before baron001 1.png)
            successful_pages = result["successful_pages"]
            assert successful_pages[0]["page_number"] == 1  # baron001.png
            assert successful_pages[1]["page_number"] == 2  # baron001 1.png
            
            # Test Requirement 2.3: Maximum 4 LLM calls per page
            # 3 coordination calls per page (download, ocr, storage)
            # OCR tool internally makes 3 passes
            total_coordination_calls = mock_download_tool._run.call_count + mock_ocr_tool._run.call_count + mock_storage_tool._run.call_count
            assert total_coordination_calls == 6  # 2 pages × 3 calls per page
            
            # Test that OCR metadata is properly structured
            detailed_results = result["detailed_results"]
            for page_result in detailed_results:
                ocr_result = page_result["ocr_result"]
                assert ocr_result["ocr_passes"] == 3
                assert ocr_result["model_used"] == "gpt-4o"
                assert "processing_stats" in ocr_result
                assert "unclear_sections" in ocr_result
            
            logger.info("✅ All requirements compliance tests passed!")
            return True

def test_error_handling_requirement_6_4():
    """Test Requirement 6.4: Error handling without stopping entire process."""
    
    test_inputs = {
        "client_user_id": "test-client-123",
        "google_drive_folder_path": "test/folder/path",
        "language": "en"
    }
    
    # Mock 3 files where middle one fails
    mock_files = [
        {"file_id": "file1", "name": "baron001.png", "file_name": "baron001.png", "mime_type": "image/png"},
        {"file_id": "file2", "name": "baron001 1.png", "file_name": "baron001 1.png", "mime_type": "image/png"},
        {"file_id": "file3", "name": "baron001 2.png", "file_name": "baron001 2.png", "mime_type": "image/png"}
    ]
    
    with patch('crews.book_ingestion_crew.crew.get_files_from_drive') as mock_get_files:
        mock_get_files.return_value = mock_files
        
        with patch('crews.book_ingestion_crew.crew.GoogleDriveDownloadTool') as mock_download_tool_class, \
             patch('crews.book_ingestion_crew.crew.ImageViewerTool') as mock_ocr_tool_class, \
             patch('crews.book_ingestion_crew.crew.SyncDBStorageTool') as mock_storage_tool_class:
            
            mock_download_tool = Mock()
            mock_ocr_tool = Mock()
            mock_storage_tool = Mock()
            
            mock_download_tool_class.return_value = mock_download_tool
            mock_ocr_tool_class.return_value = mock_ocr_tool
            mock_storage_tool_class.return_value = mock_storage_tool
            
            # Mock responses - make middle file fail
            def download_side_effect(*args, **kwargs):
                file_name = kwargs.get('file_name', '')
                if 'baron001 1.png' in file_name:
                    return json.dumps({"status": "error", "error": "Download failed for middle file"})
                return json.dumps({"status": "success", "local_path": "/tmp/test.png"})
            
            mock_download_tool._run.side_effect = download_side_effect
            
            mock_ocr_tool._run.return_value = json.dumps({
                "status": "success", "transcription": "Test text", "processing_stats": {},
                "unclear_sections": [], "ocr_passes": 3, "model_used": "gpt-4o"
            })
            
            mock_storage_tool._run.return_value = json.dumps({"status": "success", "page_id": "page-123"})
            
            # Run orchestrator
            result = manual_loop_orchestrator(test_inputs)
            
            # Verify that processing continued despite middle file failure
            assert result["status"] == "completed"
            assert result["total_pages"] == 3
            assert result["processed_successfully"] == 2  # First and third files
            assert result["failed"] == 1  # Middle file
            
            # Verify error details
            failed_pages = result["failed_pages"]
            assert len(failed_pages) == 1
            assert failed_pages[0]["page_number"] == 2  # baron001 1.png
            assert "Download failed for middle file" in failed_pages[0]["error"]
            
            # Verify successful pages
            successful_pages = result["successful_pages"]
            assert len(successful_pages) == 2
            page_numbers = [p["page_number"] for p in successful_pages]
            assert 1 in page_numbers  # baron001.png
            assert 3 in page_numbers  # baron001 2.png
            
            logger.info("✅ Error handling requirement 6.4 test passed!")
            return True

def test_file_discovery_and_sorting():
    """Test file discovery and sorting logic (Requirement 6.3)."""
    
    test_inputs = {
        "client_user_id": "test-client-123",
        "google_drive_folder_path": "test/folder/path",
        "language": "en"
    }
    
    # Mock files in random order to test sorting
    mock_files = [
        {"file_id": "file3", "name": "baron001 2.png", "file_name": "baron001 2.png", "mime_type": "image/png"},
        {"file_id": "file1", "name": "baron001.png", "file_name": "baron001.png", "mime_type": "image/png"},
        {"file_id": "file4", "name": "baron001 24.png", "file_name": "baron001 24.png", "mime_type": "image/png"},
        {"file_id": "file2", "name": "baron001 1.png", "file_name": "baron001 1.png", "mime_type": "image/png"},
    ]
    
    with patch('crews.book_ingestion_crew.crew.get_files_from_drive') as mock_get_files:
        mock_get_files.return_value = mock_files
        
        with patch('crews.book_ingestion_crew.crew.GoogleDriveDownloadTool') as mock_download_tool_class, \
             patch('crews.book_ingestion_crew.crew.ImageViewerTool') as mock_ocr_tool_class, \
             patch('crews.book_ingestion_crew.crew.SyncDBStorageTool') as mock_storage_tool_class:
            
            # Mock all tools to succeed
            mock_download_tool = Mock()
            mock_ocr_tool = Mock()
            mock_storage_tool = Mock()
            
            mock_download_tool_class.return_value = mock_download_tool
            mock_ocr_tool_class.return_value = mock_ocr_tool
            mock_storage_tool_class.return_value = mock_storage_tool
            
            mock_download_tool._run.return_value = json.dumps({"status": "success", "local_path": "/tmp/test.png"})
            mock_ocr_tool._run.return_value = json.dumps({
                "status": "success", "transcription": "Test", "processing_stats": {},
                "unclear_sections": [], "ocr_passes": 3, "model_used": "gpt-4o"
            })
            mock_storage_tool._run.return_value = json.dumps({"status": "success", "page_id": "page-123"})
            
            # Run orchestrator
            result = manual_loop_orchestrator(test_inputs)
            
            # Verify files were processed in correct order
            successful_pages = result["successful_pages"]
            expected_order = [1, 2, 3, 25]  # baron001.png, baron001 1.png, baron001 2.png, baron001 24.png
            actual_order = [p["page_number"] for p in successful_pages]
            
            assert actual_order == expected_order, f"Expected order {expected_order}, got {actual_order}"
            
            logger.info("✅ File discovery and sorting test passed!")
            return True

if __name__ == "__main__":
    try:
        logger.info("Starting comprehensive orchestrator tests...")
        
        test_requirements_compliance()
        test_error_handling_requirement_6_4()
        test_file_discovery_and_sorting()
        
        logger.info("🎉 All comprehensive tests passed!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)