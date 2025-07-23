"""
Comprehensive Error Handling and Logging for Book Ingestion Crew

This module implements task 8 requirements:
- Error handling for individual page failures without stopping entire process
- Proper logging with context (page number, file name)
- Retry logic for transient failures
- Graceful degradation for OCR quality issues

Requirements: 6.4, 2.4
"""
import logging
import time
import json
from typing import Dict, Any, Optional, List, Callable, Union
from dataclasses import dataclass, asdict
from enum import Enum
import traceback
from pathlib import Path
import tempfile
import os

# Import retry utilities from shared library
from sparkjar_shared.utils.retry_utils import RetryConfig, retry_with_exponential_backoff

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels for categorizing failures."""
    LOW = "low"           # Minor issues that don't affect processing
    MEDIUM = "medium"     # Issues that affect quality but allow continuation
    HIGH = "high"         # Serious issues that may require attention
    CRITICAL = "critical" # Issues that prevent processing


class ErrorCategory(Enum):
    """Categories of errors that can occur during processing."""
    NETWORK = "network"                    # Network connectivity issues
    API_RATE_LIMIT = "api_rate_limit"     # API rate limiting
    FILE_ACCESS = "file_access"           # File system access issues
    GOOGLE_DRIVE = "google_drive"         # Google Drive API issues
    OCR_PROCESSING = "ocr_processing"     # OCR/vision model issues
    DATABASE = "database"                 # Database connectivity/storage issues
    VALIDATION = "validation"             # Input validation failures
    AUTHENTICATION = "authentication"     # Authentication/authorization issues
    RESOURCE_EXHAUSTION = "resource_exhaustion"  # Memory/disk space issues
    MODEL_CONFIGURATION = "model_configuration"  # LiteLLM/Model compatibility issues
    UNKNOWN = "unknown"                   # Unclassified errors


@dataclass
class ProcessingError:
    """Structured error information for detailed logging and analysis."""
    error_type: str
    error_message: str
    error_category: ErrorCategory
    severity: ErrorSeverity
    page_number: Optional[int] = None
    file_name: Optional[str] = None
    file_id: Optional[str] = None
    timestamp: float = None
    stack_trace: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    retry_count: int = 0
    recoverable: bool = True
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging and storage."""
        result = asdict(self)
        result['error_category'] = self.error_category.value
        result['severity'] = self.severity.value
        return result


class BookIngestionErrorHandler:
    """
    Comprehensive error handler for book ingestion crew operations.
    
    Provides:
    - Structured error logging with context
    - Retry logic for transient failures
    - Error categorization and severity assessment
    - Graceful degradation strategies
    - Individual page failure isolation
    """
    
    def __init__(self, logger_instance: Optional[logging.Logger] = None):
        """Initialize error handler with optional custom logger."""
        self.logger = logger_instance or logger
        self.error_history: List[ProcessingError] = []
        self.retry_configs = self._setup_retry_configs()
        self.temp_files_to_cleanup: List[str] = []
    
    def _setup_retry_configs(self) -> Dict[ErrorCategory, RetryConfig]:
        """Setup retry configurations for different error categories."""
        return {
            ErrorCategory.NETWORK: RetryConfig(
                max_retries=3,
                initial_delay=2.0,
                exponential_base=2.0,
                max_delay=30.0,
                jitter=True
            ),
            ErrorCategory.API_RATE_LIMIT: RetryConfig(
                max_retries=5,
                initial_delay=5.0,
                exponential_base=2.0,
                max_delay=120.0,
                jitter=True
            ),
            ErrorCategory.GOOGLE_DRIVE: RetryConfig(
                max_retries=3,
                initial_delay=1.0,
                exponential_base=2.0,
                max_delay=15.0,
                jitter=True
            ),
            ErrorCategory.DATABASE: RetryConfig(
                max_retries=3,
                initial_delay=1.0,
                exponential_base=2.0,
                max_delay=10.0,
                jitter=True
            ),
            ErrorCategory.OCR_PROCESSING: RetryConfig(
                max_retries=2,  # Limited retries for OCR to avoid excessive costs
                initial_delay=3.0,
                exponential_base=1.5,
                max_delay=20.0,
                jitter=True
            )
        }
    
    def categorize_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> ErrorCategory:
        """Categorize an error based on its type and message."""
        error_msg = str(error).lower()
        error_type = type(error).__name__.lower()
        
        # Model configuration/LiteLLM errors (check first as these are common)
        if any(keyword in error_msg for keyword in [
            'litellm', 'unknown parameter', 'invalid parameter',
            'model not found', 'unsupported model', 'gpt-4.1',
            'openai.error', 'invalid request error'
        ]):
            return ErrorCategory.MODEL_CONFIGURATION
        
        # Network-related errors
        if any(keyword in error_msg for keyword in [
            'connection', 'timeout', 'network', 'dns', 'socket',
            'connectionerror', 'timeouterror', 'httperror'
        ]):
            return ErrorCategory.NETWORK
        
        # API rate limiting
        if any(keyword in error_msg for keyword in [
            'rate limit', 'quota', 'too many requests', '429',
            'rate_limit_exceeded', 'quota_exceeded'
        ]):
            return ErrorCategory.API_RATE_LIMIT
        
        # Google Drive specific
        if any(keyword in error_msg for keyword in [
            'google drive', 'drive api', 'file not found', 'permission denied',
            'invalid file id', 'drive service'
        ]):
            return ErrorCategory.GOOGLE_DRIVE
        
        # Database errors
        if any(keyword in error_msg for keyword in [
            'database', 'sqlalchemy', 'connection pool', 'postgresql',
            'psycopg2', 'database connection', 'transaction'
        ]):
            return ErrorCategory.DATABASE
        
        # OCR/Vision processing
        if any(keyword in error_msg for keyword in [
            'openai', 'gpt-4o', 'vision', 'image processing', 'ocr',
            'base64', 'image format', 'model error'
        ]):
            return ErrorCategory.OCR_PROCESSING
        
        # File access issues
        if any(keyword in error_msg for keyword in [
            'file not found', 'permission denied', 'no such file',
            'access denied', 'disk space', 'temporary file'
        ]):
            return ErrorCategory.FILE_ACCESS
        
        # Validation errors
        if any(keyword in error_msg for keyword in [
            'validation', 'invalid input', 'schema', 'required field',
            'pydantic', 'validation error'
        ]):
            return ErrorCategory.VALIDATION
        
        # Authentication issues
        if any(keyword in error_msg for keyword in [
            'authentication', 'authorization', 'api key', 'token',
            'unauthorized', 'forbidden', '401', '403'
        ]):
            return ErrorCategory.AUTHENTICATION
        
        # Resource exhaustion
        if any(keyword in error_msg for keyword in [
            'memory', 'disk space', 'resource', 'out of memory',
            'no space left', 'resource exhausted'
        ]):
            return ErrorCategory.RESOURCE_EXHAUSTION
        
        return ErrorCategory.UNKNOWN
    
    def assess_severity(self, error: Exception, category: ErrorCategory, context: Optional[Dict[str, Any]] = None) -> ErrorSeverity:
        """Assess the severity of an error."""
        error_msg = str(error).lower()
        
        # Critical errors that prevent processing
        if category in [ErrorCategory.AUTHENTICATION, ErrorCategory.RESOURCE_EXHAUSTION]:
            return ErrorSeverity.CRITICAL
        
        if any(keyword in error_msg for keyword in [
            'critical', 'fatal', 'system error', 'out of memory'
        ]):
            return ErrorSeverity.CRITICAL
        
        # High severity errors
        if category in [ErrorCategory.DATABASE, ErrorCategory.VALIDATION]:
            return ErrorSeverity.HIGH
        
        if any(keyword in error_msg for keyword in [
            'database connection', 'invalid schema', 'required field missing'
        ]):
            return ErrorSeverity.HIGH
        
        # Medium severity errors
        if category in [ErrorCategory.OCR_PROCESSING, ErrorCategory.GOOGLE_DRIVE]:
            return ErrorSeverity.MEDIUM
        
        # Low severity errors (transient network issues, etc.)
        if category in [ErrorCategory.NETWORK, ErrorCategory.API_RATE_LIMIT]:
            return ErrorSeverity.LOW
        
        return ErrorSeverity.MEDIUM
    
    def is_recoverable(self, error: Exception, category: ErrorCategory) -> bool:
        """Determine if an error is recoverable through retries."""
        # Non-recoverable error categories
        if category in [ErrorCategory.VALIDATION, ErrorCategory.AUTHENTICATION, ErrorCategory.MODEL_CONFIGURATION]:
            return False
        
        error_msg = str(error).lower()
        
        # Non-recoverable error patterns
        non_recoverable_patterns = [
            'invalid api key',
            'authentication failed',
            'permission denied',
            'file not found',
            'invalid file id',
            'schema validation failed',
            'required field missing',
            'unsupported format',
            # LiteLLM/Model compatibility errors
            'litellm',
            'unknown parameter',
            'invalid parameter',
            'model not found',
            'unsupported model',
            'gpt-4.1',  # Specific to our custom models
            'openai.error',
            'invalid request error'
        ]
        
        if any(pattern in error_msg for pattern in non_recoverable_patterns):
            return False
        
        return True
    
    def log_error(self, 
                  error: Exception, 
                  page_number: Optional[int] = None,
                  file_name: Optional[str] = None,
                  file_id: Optional[str] = None,
                  context: Optional[Dict[str, Any]] = None,
                  retry_count: int = 0) -> ProcessingError:
        """
        Log an error with full context and structured information.
        
        Args:
            error: The exception that occurred
            page_number: Page number being processed (if applicable)
            file_name: File name being processed (if applicable)
            file_id: Google Drive file ID (if applicable)
            context: Additional context information
            retry_count: Current retry attempt number
            
        Returns:
            ProcessingError object with structured error information
        """
        category = self.categorize_error(error, context)
        severity = self.assess_severity(error, category, context)
        recoverable = self.is_recoverable(error, category)
        
        processing_error = ProcessingError(
            error_type=type(error).__name__,
            error_message=str(error),
            error_category=category,
            severity=severity,
            page_number=page_number,
            file_name=file_name,
            file_id=file_id,
            stack_trace=traceback.format_exc(),
            context=context or {},
            retry_count=retry_count,
            recoverable=recoverable
        )
        
        # Add to error history
        self.error_history.append(processing_error)
        
        # Log with appropriate level based on severity
        log_data = processing_error.to_dict()
        
        if severity == ErrorSeverity.CRITICAL:
            self.logger.critical(f"CRITICAL ERROR - Page {page_number} ({file_name}): {error}", extra=log_data)
        elif severity == ErrorSeverity.HIGH:
            self.logger.error(f"HIGH SEVERITY ERROR - Page {page_number} ({file_name}): {error}", extra=log_data)
        elif severity == ErrorSeverity.MEDIUM:
            self.logger.warning(f"MEDIUM SEVERITY ERROR - Page {page_number} ({file_name}): {error}", extra=log_data)
        else:
            self.logger.info(f"LOW SEVERITY ERROR - Page {page_number} ({file_name}): {error}", extra=log_data)
        
        return processing_error
    
    async def execute_with_retry(self,
                                func: Callable,
                                *args,
                                page_number: Optional[int] = None,
                                file_name: Optional[str] = None,
                                file_id: Optional[str] = None,
                                context: Optional[Dict[str, Any]] = None,
                                **kwargs) -> Any:
        """
        Execute a function with automatic retry logic based on error category.
        
        Args:
            func: Function to execute
            page_number: Page number for context
            file_name: File name for context
            file_id: File ID for context
            context: Additional context
            *args, **kwargs: Arguments for the function
            
        Returns:
            Function result
            
        Raises:
            Last exception if all retries are exhausted
        """
        last_error = None
        retry_count = 0
        
        while True:
            try:
                # Execute the function
                if hasattr(func, '__call__'):
                    result = func(*args, **kwargs)
                    # Handle both sync and async functions
                    if hasattr(result, '__await__'):
                        result = await result
                    return result
                else:
                    raise ValueError(f"Invalid function provided: {func}")
                    
            except Exception as error:
                last_error = error
                
                # Log the error with context
                processing_error = self.log_error(
                    error=error,
                    page_number=page_number,
                    file_name=file_name,
                    file_id=file_id,
                    context=context,
                    retry_count=retry_count
                )
                
                # Check if error is recoverable
                if not processing_error.recoverable:
                    self.logger.error(f"Non-recoverable error for page {page_number} ({file_name}): {error}")
                    raise error
                
                # Get retry configuration for this error category
                retry_config = self.retry_configs.get(processing_error.error_category)
                if not retry_config or retry_count >= retry_config.max_retries:
                    self.logger.error(f"Max retries ({retry_count}) exceeded for page {page_number} ({file_name}): {error}")
                    raise error
                
                # Calculate delay and wait
                delay = retry_config.get_delay(retry_count)
                self.logger.info(f"Retrying page {page_number} ({file_name}) in {delay:.2f}s (attempt {retry_count + 1}/{retry_config.max_retries + 1})")
                
                # Use asyncio.sleep for async context, time.sleep for sync
                try:
                    import asyncio
                    await asyncio.sleep(delay)
                except RuntimeError:
                    # Not in async context
                    time.sleep(delay)
                
                retry_count += 1
    
    def handle_ocr_degradation(self, 
                              ocr_result: Dict[str, Any], 
                              page_number: int, 
                              file_name: str) -> Dict[str, Any]:
        """
        Handle OCR quality issues with graceful degradation.
        
        Implements requirement 2.4 for graceful degradation of OCR quality issues.
        
        Args:
            ocr_result: OCR processing result
            page_number: Page number
            file_name: File name
            
        Returns:
            Enhanced OCR result with quality assessment and degradation handling
        """
        try:
            # Extract quality indicators from OCR result
            transcription = ocr_result.get('transcription', '')
            processing_stats = ocr_result.get('processing_stats', {})
            unclear_sections = ocr_result.get('unclear_sections', [])
            
            # Assess OCR quality
            quality_score = self._assess_ocr_quality(transcription, processing_stats, unclear_sections)
            
            # Apply degradation strategies based on quality
            if quality_score < 0.3:  # Very poor quality
                self.logger.warning(f"Very poor OCR quality ({quality_score:.2f}) for page {page_number} ({file_name})")
                ocr_result['quality_warning'] = 'very_poor'
                ocr_result['degradation_applied'] = 'minimal_processing'
                
                # For very poor quality, mark as requiring manual review
                ocr_result['requires_manual_review'] = True
                ocr_result['transcription'] = f"[POOR_QUALITY_OCR] {transcription}"
                
            elif quality_score < 0.6:  # Poor quality
                self.logger.info(f"Poor OCR quality ({quality_score:.2f}) for page {page_number} ({file_name})")
                ocr_result['quality_warning'] = 'poor'
                ocr_result['degradation_applied'] = 'quality_markers'
                
                # Add quality markers to unclear sections
                if unclear_sections:
                    ocr_result['transcription'] = self._add_quality_markers(transcription, unclear_sections)
                
            elif quality_score < 0.8:  # Moderate quality
                self.logger.debug(f"Moderate OCR quality ({quality_score:.2f}) for page {page_number} ({file_name})")
                ocr_result['quality_warning'] = 'moderate'
                ocr_result['degradation_applied'] = 'uncertainty_markers'
                
            else:  # Good quality
                self.logger.debug(f"Good OCR quality ({quality_score:.2f}) for page {page_number} ({file_name})")
                ocr_result['quality_warning'] = None
                ocr_result['degradation_applied'] = None
            
            # Add quality assessment to metadata
            ocr_result['quality_score'] = quality_score
            ocr_result['quality_assessment'] = {
                'score': quality_score,
                'total_words': len(transcription.split()) if transcription else 0,
                'unclear_word_count': len(unclear_sections),
                'clarity_ratio': 1.0 - (len(unclear_sections) / max(len(transcription.split()), 1)) if transcription else 0.0
            }
            
            return ocr_result
            
        except Exception as e:
            self.logger.error(f"Error in OCR degradation handling for page {page_number} ({file_name}): {e}")
            # Return original result if degradation handling fails
            ocr_result['degradation_error'] = str(e)
            return ocr_result
    
    def _assess_ocr_quality(self, 
                           transcription: str, 
                           processing_stats: Dict[str, Any], 
                           unclear_sections: List[str]) -> float:
        """Assess OCR quality based on various indicators."""
        if not transcription:
            return 0.0
        
        total_words = len(transcription.split())
        if total_words == 0:
            return 0.0
        
        # Base quality score
        quality_score = 1.0
        
        # Penalize for unclear sections
        unclear_ratio = len(unclear_sections) / total_words
        quality_score -= unclear_ratio * 0.5
        
        # Penalize for very short transcriptions (likely incomplete)
        if total_words < 10:
            quality_score -= 0.3
        
        # Penalize for excessive special characters or garbled text
        special_char_ratio = sum(1 for c in transcription if not c.isalnum() and c not in ' .,!?;:-()[]{}') / len(transcription)
        if special_char_ratio > 0.2:
            quality_score -= special_char_ratio * 0.3
        
        # Bonus for processing statistics indicating good recognition
        if processing_stats:
            normal_transcription = processing_stats.get('normal_transcription', 0)
            total_processed = processing_stats.get('total_words', total_words)
            if total_processed > 0:
                normal_ratio = normal_transcription / total_processed
                quality_score += normal_ratio * 0.2
        
        return max(0.0, min(1.0, quality_score))
    
    def _add_quality_markers(self, transcription: str, unclear_sections: List[str]) -> str:
        """Add quality markers to transcription for unclear sections."""
        result = transcription
        
        # Add uncertainty markers around unclear sections
        for unclear in unclear_sections:
            if unclear in result:
                result = result.replace(unclear, f"[UNCLEAR: {unclear}]")
        
        return result
    
    def cleanup_temp_files(self):
        """Clean up temporary files created during processing."""
        for temp_file in self.temp_files_to_cleanup:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    self.logger.debug(f"Cleaned up temporary file: {temp_file}")
            except Exception as e:
                self.logger.warning(f"Failed to cleanup temporary file {temp_file}: {e}")
        
        self.temp_files_to_cleanup.clear()
    
    def add_temp_file(self, file_path: str):
        """Add a temporary file to the cleanup list."""
        self.temp_files_to_cleanup.append(file_path)
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get a summary of all errors encountered during processing."""
        if not self.error_history:
            return {"total_errors": 0, "error_categories": {}, "severity_breakdown": {}}
        
        # Count errors by category
        category_counts = {}
        severity_counts = {}
        
        for error in self.error_history:
            category = error.error_category.value
            severity = error.severity.value
            
            category_counts[category] = category_counts.get(category, 0) + 1
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        return {
            "total_errors": len(self.error_history),
            "error_categories": category_counts,
            "severity_breakdown": severity_counts,
            "recoverable_errors": sum(1 for e in self.error_history if e.recoverable),
            "non_recoverable_errors": sum(1 for e in self.error_history if not e.recoverable),
            "pages_with_errors": len(set(e.page_number for e in self.error_history if e.page_number)),
            "most_common_category": max(category_counts.items(), key=lambda x: x[1])[0] if category_counts else None,
            "highest_severity": max(severity_counts.keys()) if severity_counts else None
        }
    
    def should_continue_processing(self, current_page: int, total_pages: int) -> bool:
        """
        Determine if processing should continue based on error history.
        
        Implements intelligent stopping criteria to prevent excessive failures.
        """
        if not self.error_history:
            return True
        
        # Get recent errors (last 5 pages)
        recent_errors = [e for e in self.error_history if e.page_number and e.page_number >= current_page - 5]
        
        # Stop if too many critical errors
        critical_errors = [e for e in recent_errors if e.severity == ErrorSeverity.CRITICAL]
        if len(critical_errors) >= 3:
            self.logger.critical(f"Stopping processing due to {len(critical_errors)} critical errors in recent pages")
            return False
        
        # Stop if error rate is too high
        if len(recent_errors) >= 4 and current_page > 5:  # More than 80% error rate
            self.logger.error(f"Stopping processing due to high error rate: {len(recent_errors)}/5 recent pages failed")
            return False
        
        # Stop if all recent errors are non-recoverable
        if len(recent_errors) >= 3 and all(not e.recoverable for e in recent_errors):
            self.logger.error("Stopping processing due to consecutive non-recoverable errors")
            return False
        
        return True


def create_error_handler(logger_instance: Optional[logging.Logger] = None) -> BookIngestionErrorHandler:
    """
    Factory function to create a BookIngestionErrorHandler instance.
    
    Args:
        logger_instance: Optional custom logger instance
        
    Returns:
        Configured BookIngestionErrorHandler
    """
    return BookIngestionErrorHandler(logger_instance)