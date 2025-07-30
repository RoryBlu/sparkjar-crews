"""
Performance monitoring and metrics collection for book ingestion crew.

This module implements comprehensive performance tracking for:
- Processing time per page and total execution time
- LLM call counting and validation (max 4 per page)
- Database transaction performance tracking
- Resource usage metrics
- Quality metrics and error rates

The monitoring system provides real-time tracking during execution
and generates detailed performance reports after completion.
"""

import json
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

try:
    import psutil
except ImportError:  # pragma: no cover - fallback if psutil not installed
    psutil = None

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics being tracked."""

    TIMING = "timing"
    COUNT = "count"
    SIZE = "size"
    RATE = "rate"
    QUALITY = "quality"


@dataclass
class PageMetrics:
    """Metrics for a single page processing."""

    page_number: int
    file_name: str
    start_time: float
    end_time: Optional[float] = None

    # Timing metrics
    download_time: Optional[float] = None
    ocr_time: Optional[float] = None
    storage_time: Optional[float] = None
    total_time: Optional[float] = None

    # LLM metrics
    llm_calls: int = 0
    llm_tokens_used: int = 0
    ocr_passes: int = 0

    # File metrics
    file_size_bytes: Optional[int] = None
    text_length: Optional[int] = None

    # Quality metrics
    ocr_quality_score: Optional[float] = None
    unclear_sections: int = 0
    requires_review: bool = False

    # Error tracking
    errors: List[Dict[str, Any]] = field(default_factory=list)
    retry_count: int = 0

    def calculate_total_time(self):
        """Calculate total processing time for the page."""
        if self.end_time:
            self.total_time = self.end_time - self.start_time


@dataclass
class PerformanceReport:
    """Complete performance report for a book ingestion job."""

    job_id: str
    start_time: datetime
    end_time: Optional[datetime] = None

    # Overall metrics
    total_pages: int = 0
    successful_pages: int = 0
    failed_pages: int = 0

    # Timing metrics
    total_execution_time: Optional[float] = None
    average_page_time: Optional[float] = None
    fastest_page_time: Optional[float] = None
    slowest_page_time: Optional[float] = None

    # LLM metrics
    total_llm_calls: int = 0
    average_llm_calls_per_page: float = 0.0
    pages_exceeding_llm_limit: int = 0
    total_tokens_used: int = 0

    # Database metrics
    total_db_transactions: int = 0
    average_db_time: Optional[float] = None
    db_errors: int = 0

    # Quality metrics
    average_quality_score: float = 0.0
    high_quality_pages: int = 0
    low_quality_pages: int = 0
    pages_requiring_review: int = 0

    # Resource metrics (would require psutil)
    peak_memory_usage_mb: Optional[float] = None
    average_cpu_percent: Optional[float] = None

    # Detailed page metrics
    page_metrics: List[PageMetrics] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary for JSON serialization."""
        return {
            "job_id": self.job_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "summary": {
                "total_pages": self.total_pages,
                "successful_pages": self.successful_pages,
                "failed_pages": self.failed_pages,
                "success_rate": (
                    f"{(self.successful_pages / self.total_pages * 100):.1f}%"
                    if self.total_pages > 0
                    else "0%"
                ),
            },
            "timing": {
                "total_execution_time": (
                    f"{self.total_execution_time:.2f}s"
                    if self.total_execution_time
                    else None
                ),
                "average_page_time": (
                    f"{self.average_page_time:.2f}s" if self.average_page_time else None
                ),
                "fastest_page_time": (
                    f"{self.fastest_page_time:.2f}s" if self.fastest_page_time else None
                ),
                "slowest_page_time": (
                    f"{self.slowest_page_time:.2f}s" if self.slowest_page_time else None
                ),
            },
            "llm_usage": {
                "total_calls": self.total_llm_calls,
                "average_calls_per_page": f"{self.average_llm_calls_per_page:.1f}",
                "pages_exceeding_limit": self.pages_exceeding_llm_limit,
                "total_tokens": self.total_tokens_used,
                "compliance": "PASS" if self.pages_exceeding_llm_limit == 0 else "FAIL",
            },
            "database": {
                "total_transactions": self.total_db_transactions,
                "average_time": (
                    f"{self.average_db_time:.3f}s" if self.average_db_time else None
                ),
                "errors": self.db_errors,
            },
            "quality": {
                "average_score": f"{self.average_quality_score:.2f}",
                "high_quality_pages": self.high_quality_pages,
                "low_quality_pages": self.low_quality_pages,
                "requiring_review": self.pages_requiring_review,
            },
            "resources": {
                "peak_memory_mb": (
                    f"{self.peak_memory_usage_mb:.1f}"
                    if self.peak_memory_usage_mb
                    else None
                ),
                "average_cpu_percent": (
                    f"{self.average_cpu_percent:.1f}%"
                    if self.average_cpu_percent
                    else None
                ),
            },
        }


class PerformanceMonitor:
    """
    Performance monitoring system for book ingestion crew.

    Tracks and reports on all aspects of crew performance including:
    - Processing times for each operation
    - LLM usage and compliance with limits
    - Database performance
    - Resource utilization
    - Quality metrics
    """

    def __init__(self, job_id: str, max_llm_calls_per_page: int = 4):
        """
        Initialize performance monitor.

        Args:
            job_id: Unique identifier for the job being monitored
            max_llm_calls_per_page: Maximum allowed LLM calls per page (default: 4)
        """
        self.job_id = job_id
        self.max_llm_calls_per_page = max_llm_calls_per_page

        self.report = PerformanceReport(job_id=job_id, start_time=datetime.now())

        self.current_page_metrics: Optional[PageMetrics] = None
        self.operation_timers: Dict[str, float] = {}

        # Resource tracking
        self.memory_samples: List[float] = []
        self.cpu_samples: List[float] = []

        logger.info(f"Performance monitor initialized for job {job_id}")

    def start_page_processing(self, page_number: int, file_name: str) -> None:
        """Start tracking metrics for a new page."""
        self.current_page_metrics = PageMetrics(
            page_number=page_number, file_name=file_name, start_time=time.time()
        )
        self.report.total_pages += 1
        logger.debug(f"Started monitoring page {page_number}: {file_name}")

    def start_operation(self, operation: str) -> None:
        """Start timing a specific operation."""
        self.operation_timers[operation] = time.time()
        logger.debug(f"Started timing operation: {operation}")

    def end_operation(self, operation: str) -> float:
        """
        End timing an operation and return elapsed time.

        Args:
            operation: Name of the operation

        Returns:
            Elapsed time in seconds
        """
        if operation not in self.operation_timers:
            logger.warning(f"Operation {operation} was not started")
            return 0.0

        elapsed = time.time() - self.operation_timers[operation]
        del self.operation_timers[operation]

        if self.current_page_metrics:
            if operation == "download":
                self.current_page_metrics.download_time = elapsed
            elif operation == "ocr":
                self.current_page_metrics.ocr_time = elapsed
            elif operation == "storage":
                self.current_page_metrics.storage_time = elapsed
                self.report.total_db_transactions += 1

        logger.debug(f"Operation {operation} completed in {elapsed:.2f}s")
        return elapsed

    def record_llm_call(self, tokens_used: int = 0) -> None:
        """Record an LLM API call."""
        if self.current_page_metrics:
            self.current_page_metrics.llm_calls += 1
            self.current_page_metrics.llm_tokens_used += tokens_used

        self.report.total_llm_calls += 1
        self.report.total_tokens_used += tokens_used

    def record_ocr_pass(self) -> None:
        """Record an OCR pass."""
        if self.current_page_metrics:
            self.current_page_metrics.ocr_passes += 1

    def record_file_metrics(self, file_size: int, text_length: int) -> None:
        """Record file size and text length metrics."""
        if self.current_page_metrics:
            self.current_page_metrics.file_size_bytes = file_size
            self.current_page_metrics.text_length = text_length

    def record_quality_metrics(
        self, quality_score: float, unclear_sections: int, requires_review: bool
    ) -> None:
        """Record OCR quality metrics."""
        if self.current_page_metrics:
            self.current_page_metrics.ocr_quality_score = quality_score
            self.current_page_metrics.unclear_sections = unclear_sections
            self.current_page_metrics.requires_review = requires_review

    def record_error(self, error: Exception, operation: str) -> None:
        """Record an error during page processing."""
        if self.current_page_metrics:
            self.current_page_metrics.errors.append(
                {"operation": operation, "error": str(error), "timestamp": time.time()}
            )

    def record_retry(self) -> None:
        """Record a retry attempt."""
        if self.current_page_metrics:
            self.current_page_metrics.retry_count += 1

    def end_page_processing(self, success: bool) -> None:
        """Complete tracking for the current page."""
        if not self.current_page_metrics:
            logger.warning("No current page metrics to end")
            return

        self.current_page_metrics.end_time = time.time()
        self.current_page_metrics.calculate_total_time()

        # Update counters
        if success:
            self.report.successful_pages += 1
        else:
            self.report.failed_pages += 1

        # Check LLM limit compliance
        if self.current_page_metrics.llm_calls > self.max_llm_calls_per_page:
            self.report.pages_exceeding_llm_limit += 1
            logger.warning(
                f"Page {self.current_page_metrics.page_number} exceeded LLM limit: "
                f"{self.current_page_metrics.llm_calls} calls (max: {self.max_llm_calls_per_page})"
            )

        # Update quality metrics
        if self.current_page_metrics.ocr_quality_score is not None:
            if self.current_page_metrics.ocr_quality_score > 0.8:
                self.report.high_quality_pages += 1
            elif self.current_page_metrics.ocr_quality_score < 0.6:
                self.report.low_quality_pages += 1

        if self.current_page_metrics.requires_review:
            self.report.pages_requiring_review += 1

        # Add to report
        self.report.page_metrics.append(self.current_page_metrics)

        # Sample resources
        self._sample_resources()

        logger.info(
            f"Completed page {self.current_page_metrics.page_number} in "
            f"{self.current_page_metrics.total_time:.2f}s (success: {success})"
        )

        self.current_page_metrics = None

    def _sample_resources(self) -> None:
        """Sample current CPU and memory usage using psutil if available."""
        if psutil is None:
            return

        process = psutil.Process(os.getpid())

        try:
            mem_mb = process.memory_info().rss / 1024 / 1024
            self.memory_samples.append(mem_mb)
            if (
                self.report.peak_memory_usage_mb is None
                or mem_mb > self.report.peak_memory_usage_mb
            ):
                self.report.peak_memory_usage_mb = mem_mb

            cpu_percent = process.cpu_percent(interval=None)
            self.cpu_samples.append(cpu_percent)
        except Exception as exc:  # pragma: no cover - defensive
            logger.debug(f"Resource sampling failed: {exc}")

    def finalize_report(self) -> PerformanceReport:
        """
        Finalize the performance report with calculated metrics.

        Returns:
            Complete performance report
        """
        self.report.end_time = datetime.now()
        self.report.total_execution_time = (
            self.report.end_time - self.report.start_time
        ).total_seconds()

        # Calculate timing metrics
        if self.report.page_metrics:
            page_times = [
                m.total_time
                for m in self.report.page_metrics
                if m.total_time is not None
            ]
            if page_times:
                self.report.average_page_time = sum(page_times) / len(page_times)
                self.report.fastest_page_time = min(page_times)
                self.report.slowest_page_time = max(page_times)

        # Calculate LLM metrics
        if self.report.total_pages > 0:
            self.report.average_llm_calls_per_page = (
                self.report.total_llm_calls / self.report.total_pages
            )

        # Calculate database metrics
        db_times = [
            m.storage_time
            for m in self.report.page_metrics
            if m.storage_time is not None
        ]
        if db_times:
            self.report.average_db_time = sum(db_times) / len(db_times)

        # Calculate quality metrics
        quality_scores = [
            m.ocr_quality_score
            for m in self.report.page_metrics
            if m.ocr_quality_score is not None
        ]
        if quality_scores:
            self.report.average_quality_score = sum(quality_scores) / len(
                quality_scores
            )

        if self.cpu_samples:
            self.report.average_cpu_percent = sum(self.cpu_samples) / len(
                self.cpu_samples
            )

        if self.memory_samples and self.report.peak_memory_usage_mb is None:
            self.report.peak_memory_usage_mb = max(self.memory_samples)

        logger.info(f"Performance report finalized for job {self.job_id}")
        return self.report

    def get_current_stats(self) -> Dict[str, Any]:
        """Get current performance statistics."""
        return {
            "job_id": self.job_id,
            "progress": {
                "total_pages": self.report.total_pages,
                "completed": self.report.successful_pages + self.report.failed_pages,
                "success_rate": f"{(self.report.successful_pages / max(1, self.report.successful_pages + self.report.failed_pages) * 100):.1f}%",
            },
            "current_page": {
                "page_number": (
                    self.current_page_metrics.page_number
                    if self.current_page_metrics
                    else None
                ),
                "file_name": (
                    self.current_page_metrics.file_name
                    if self.current_page_metrics
                    else None
                ),
                "elapsed_time": (
                    f"{(time.time() - self.current_page_metrics.start_time):.1f}s"
                    if self.current_page_metrics
                    else None
                ),
            },
            "llm_usage": {
                "total_calls": self.report.total_llm_calls,
                "average_per_page": f"{self.report.total_llm_calls / max(1, self.report.successful_pages + self.report.failed_pages):.1f}",
            },
        }

    def log_summary(self) -> None:
        """Log a summary of the performance report."""
        report_dict = self.report.to_dict()
        logger.info("=" * 60)
        logger.info("PERFORMANCE REPORT SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Job ID: {report_dict['job_id']}")
        logger.info(f"Total Pages: {report_dict['summary']['total_pages']}")
        logger.info(f"Success Rate: {report_dict['summary']['success_rate']}")
        logger.info(f"Total Time: {report_dict['timing']['total_execution_time']}")
        logger.info(f"Average Page Time: {report_dict['timing']['average_page_time']}")
        logger.info(f"LLM Compliance: {report_dict['llm_usage']['compliance']}")
        logger.info(f"Average Quality Score: {report_dict['quality']['average_score']}")
        logger.info("=" * 60)
