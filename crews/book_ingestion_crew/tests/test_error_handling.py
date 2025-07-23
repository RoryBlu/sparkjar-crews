"""
Comprehensive unit tests for error handling module.

This module implements task 10 requirements:
- Test error categorization and severity assessment
- Test retry logic and exponential backoff
- Test OCR quality degradation handling
- Test error history and summary reporting

Requirements: 6.4, 2.4
"""
import pytest
import time
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch
import sys

# Import error handling components
sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from crews.book_ingestion_crew.error_handling import (
    BookIngestionErrorHandler,
    create_error_handler,
    ErrorCategory,
    ErrorSeverity,
    ProcessingError
)


class TestErrorHandling:
    """Comprehensive tests for error handling functionality."""
    
    @pytest.fixture
    def error_handler(self):
        """Create an error handler instance."""
        return create_error_handler()
    
    def test_error_categorization_network(self, error_handler):
        """Test categorization of network errors."""
        network_errors = [
            ConnectionError("Connection refused"),
            TimeoutError("Request timeout"),
            Exception("Network unreachable"),
            Exception("DNS resolution failed"),
            Exception("Socket error occurred")
        ]
        
        for error in network_errors:
            category = error_handler.categorize_error(error)
            assert category == ErrorCategory.NETWORK
    
    def test_error_categorization_api_rate_limit(self, error_handler):
        """Test categorization of API rate limit errors."""
        rate_limit_errors = [
            Exception("Rate limit exceeded"),
            Exception("429 Too Many Requests"),
            Exception("Quota exceeded for the day"),
            Exception("API rate_limit_exceeded")
        ]
        
        for error in rate_limit_errors:
            category = error_handler.categorize_error(error)
            assert category == ErrorCategory.API_RATE_LIMIT
    
    def test_error_categorization_google_drive(self, error_handler):
        """Test categorization of Google Drive errors."""
        drive_errors = [
            Exception("Google Drive API error"),
            Exception("File not found in Drive"),
            Exception("Permission denied for Drive file"),
            Exception("Invalid file ID provided")
        ]
        
        for error in drive_errors:
            category = error_handler.categorize_error(error)
            assert category == ErrorCategory.GOOGLE_DRIVE
    
    def test_error_categorization_database(self, error_handler):
        """Test categorization of database errors."""
        db_errors = [
            Exception("Database connection failed"),
            Exception("SQLAlchemy error occurred"),
            Exception("PostgreSQL connection pool exhausted"),
            Exception("Transaction rollback failed")
        ]
        
        for error in db_errors:
            category = error_handler.categorize_error(error)
            assert category == ErrorCategory.DATABASE
    
    def test_error_categorization_ocr(self, error_handler):
        """Test categorization of OCR processing errors."""
        ocr_errors = [
            Exception("OpenAI API error"),
            Exception("GPT-4o vision model unavailable"),
            Exception("Image processing failed"),
            Exception("Base64 encoding error")
        ]
        
        for error in ocr_errors:
            category = error_handler.categorize_error(error)
            assert category == ErrorCategory.OCR_PROCESSING
    
    def test_severity_assessment(self, error_handler):
        """Test error severity assessment."""
        # Critical errors
        critical_error = Exception("Authentication failed")
        category = error_handler.categorize_error(critical_error)
        severity = error_handler.assess_severity(critical_error, category)
        assert severity == ErrorSeverity.CRITICAL
        
        # High severity errors
        high_error = Exception("Database connection lost")
        category = error_handler.categorize_error(high_error)
        severity = error_handler.assess_severity(high_error, category)
        assert severity == ErrorSeverity.HIGH
        
        # Medium severity errors
        medium_error = Exception("OCR processing issue")
        category = error_handler.categorize_error(medium_error)
        severity = error_handler.assess_severity(medium_error, category)
        assert severity == ErrorSeverity.MEDIUM
        
        # Low severity errors
        low_error = Exception("Network timeout")
        category = error_handler.categorize_error(low_error)
        severity = error_handler.assess_severity(low_error, category)
        assert severity == ErrorSeverity.LOW
    
    def test_recoverable_error_detection(self, error_handler):
        """Test detection of recoverable vs non-recoverable errors."""
        # Recoverable errors
        recoverable_errors = [
            Exception("Network timeout"),
            Exception("Rate limit exceeded"),
            Exception("Temporary database connection issue")
        ]
        
        for error in recoverable_errors:
            category = error_handler.categorize_error(error)
            is_recoverable = error_handler.is_recoverable(error, category)
            assert is_recoverable is True
        
        # Non-recoverable errors
        non_recoverable_errors = [
            Exception("Invalid API key"),
            Exception("Authentication failed"),
            Exception("File not found"),
            Exception("Schema validation failed")
        ]
        
        for error in non_recoverable_errors:
            category = error_handler.categorize_error(error)
            is_recoverable = error_handler.is_recoverable(error, category)
            assert is_recoverable is False
    
    def test_error_logging(self, error_handler):
        """Test error logging with context."""
        error = Exception("Test error for logging")
        
        processing_error = error_handler.log_error(
            error=error,
            page_number=5,
            file_name="test_page_005.png",
            file_id="test-file-id-123",
            context={"operation": "download", "attempt": 1},
            retry_count=0
        )
        
        assert processing_error.error_type == "Exception"
        assert processing_error.error_message == "Test error for logging"
        assert processing_error.page_number == 5
        assert processing_error.file_name == "test_page_005.png"
        assert processing_error.file_id == "test-file-id-123"
        assert processing_error.context["operation"] == "download"
        assert processing_error.retry_count == 0
        assert processing_error.timestamp is not None
        assert processing_error.stack_trace is not None
    
    @pytest.mark.asyncio
    async def test_retry_logic_success(self, error_handler):
        """Test retry logic with eventual success."""
        call_count = 0
        
        def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Network timeout")
            return "Success!"
        
        result = await error_handler.execute_with_retry(
            flaky_function,
            page_number=1,
            file_name="test.png"
        )
        
        assert result == "Success!"
        assert call_count == 3  # Failed twice, succeeded on third try
    
    @pytest.mark.asyncio
    async def test_retry_logic_max_retries_exceeded(self, error_handler):
        """Test retry logic when max retries are exceeded."""
        call_count = 0
        
        def always_failing_function():
            nonlocal call_count
            call_count += 1
            raise Exception("Network timeout")
        
        with pytest.raises(Exception) as exc_info:
            await error_handler.execute_with_retry(
                always_failing_function,
                page_number=1,
                file_name="test.png"
            )
        
        assert "Network timeout" in str(exc_info.value)
        # Default network retry config has 3 max retries, so 4 total attempts
        assert call_count == 4
    
    @pytest.mark.asyncio
    async def test_retry_logic_non_recoverable(self, error_handler):
        """Test that non-recoverable errors don't trigger retries."""
        call_count = 0
        
        def non_recoverable_function():
            nonlocal call_count
            call_count += 1
            raise Exception("Authentication failed")
        
        with pytest.raises(Exception) as exc_info:
            await error_handler.execute_with_retry(
                non_recoverable_function,
                page_number=1,
                file_name="test.png"
            )
        
        assert "Authentication failed" in str(exc_info.value)
        assert call_count == 1  # No retries for non-recoverable errors
    
    def test_ocr_quality_assessment(self, error_handler):
        """Test OCR quality assessment logic."""
        # High quality transcription
        good_transcription = "This is a clear and well-transcribed text with many words."
        good_stats = {"total_words": 10, "normal_transcription": 10}
        quality_score = error_handler._assess_ocr_quality(
            good_transcription, good_stats, []
        )
        assert quality_score > 0.8
        
        # Poor quality transcription
        poor_transcription = "Th## is ###"
        poor_stats = {"total_words": 3, "normal_transcription": 1}
        quality_score = error_handler._assess_ocr_quality(
            poor_transcription, poor_stats, ["Th##", "###"]
        )
        assert quality_score < 0.5
        
        # Empty transcription
        quality_score = error_handler._assess_ocr_quality("", {}, [])
        assert quality_score == 0.0
    
    def test_ocr_degradation_handling(self, error_handler):
        """Test OCR quality degradation handling."""
        # Very poor quality
        poor_ocr_result = {
            "transcription": "### unclear ###",
            "processing_stats": {"total_words": 3, "normal_transcription": 0},
            "unclear_sections": ["###", "unclear", "###"]
        }
        
        enhanced_result = error_handler.handle_ocr_degradation(
            poor_ocr_result, page_number=1, file_name="test.png"
        )
        
        assert enhanced_result["quality_warning"] == "very_poor"
        assert enhanced_result["degradation_applied"] == "minimal_processing"
        assert enhanced_result["requires_manual_review"] is True
        assert "[POOR_QUALITY_OCR]" in enhanced_result["transcription"]
        
        # Moderate quality
        moderate_ocr_result = {
            "transcription": "This is mostly clear text with some unclear parts",
            "processing_stats": {"total_words": 9, "normal_transcription": 7},
            "unclear_sections": ["unclear"]
        }
        
        enhanced_result = error_handler.handle_ocr_degradation(
            moderate_ocr_result, page_number=2, file_name="test2.png"
        )
        
        assert enhanced_result["quality_warning"] == "moderate"
        assert enhanced_result["quality_score"] > 0.6
    
    def test_temp_file_cleanup(self, error_handler):
        """Test temporary file cleanup functionality."""
        import tempfile
        import os
        
        # Create test temp files
        temp_files = []
        for i in range(3):
            with tempfile.NamedTemporaryFile(delete=False) as f:
                temp_files.append(f.name)
                error_handler.add_temp_file(f.name)
        
        # Verify files exist
        for temp_file in temp_files:
            assert os.path.exists(temp_file)
        
        # Clean up
        error_handler.cleanup_temp_files()
        
        # Verify files are deleted
        for temp_file in temp_files:
            assert not os.path.exists(temp_file)
        
        # Verify cleanup list is empty
        assert len(error_handler.temp_files_to_cleanup) == 0
    
    def test_error_summary(self, error_handler):
        """Test error summary generation."""
        # Log various errors
        errors = [
            (Exception("Network error 1"), ErrorCategory.NETWORK, ErrorSeverity.LOW),
            (Exception("Network error 2"), ErrorCategory.NETWORK, ErrorSeverity.LOW),
            (Exception("Database error"), ErrorCategory.DATABASE, ErrorSeverity.HIGH),
            (Exception("Auth error"), ErrorCategory.AUTHENTICATION, ErrorSeverity.CRITICAL),
        ]
        
        for error, _, _ in errors:
            error_handler.log_error(
                error=error,
                page_number=1,
                file_name="test.png"
            )
        
        summary = error_handler.get_error_summary()
        
        assert summary["total_errors"] == 4
        assert summary["error_categories"]["network"] == 2
        assert summary["error_categories"]["database"] == 1
        assert summary["error_categories"]["authentication"] == 1
        assert summary["severity_breakdown"]["low"] == 2
        assert summary["severity_breakdown"]["high"] == 1
        assert summary["severity_breakdown"]["critical"] == 1
        assert summary["recoverable_errors"] == 3
        assert summary["non_recoverable_errors"] == 1
    
    def test_should_continue_processing(self, error_handler):
        """Test processing continuation logic."""
        # Should continue with no errors
        assert error_handler.should_continue_processing(1, 100) is True
        
        # Log some non-critical errors
        for i in range(2):
            error_handler.log_error(
                error=Exception("Minor error"),
                page_number=i + 1,
                file_name=f"page{i+1}.png"
            )
        
        # Should still continue
        assert error_handler.should_continue_processing(3, 100) is True
        
        # Log critical errors
        for i in range(3):
            error = Exception("Critical system error")
            processing_error = ProcessingError(
                error_type="Exception",
                error_message=str(error),
                error_category=ErrorCategory.UNKNOWN,
                severity=ErrorSeverity.CRITICAL,
                page_number=10 + i,
                recoverable=False
            )
            error_handler.error_history.append(processing_error)
        
        # Should stop due to critical errors
        assert error_handler.should_continue_processing(13, 100) is False
    
    def test_retry_config_per_category(self, error_handler):
        """Test that different error categories have appropriate retry configs."""
        configs = error_handler.retry_configs
        
        # Network errors should have moderate retries
        assert configs[ErrorCategory.NETWORK].max_retries == 3
        assert configs[ErrorCategory.NETWORK].initial_delay == 2.0
        
        # Rate limit errors should have more retries with longer delays
        assert configs[ErrorCategory.API_RATE_LIMIT].max_retries == 5
        assert configs[ErrorCategory.API_RATE_LIMIT].initial_delay == 5.0
        
        # OCR errors should have limited retries (cost consideration)
        assert configs[ErrorCategory.OCR_PROCESSING].max_retries == 2
        
        # All configs should have jitter enabled
        for config in configs.values():
            assert config.jitter is True


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])