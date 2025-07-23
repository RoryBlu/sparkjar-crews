"""
Resource management for book ingestion crew.

Implements comprehensive resource management including:
- Temporary file cleanup after processing each page
- Database connection management and pooling
- Google Drive API credential caching per client
- Memory management for large image files
- Resource usage monitoring and limits

This ensures efficient resource utilization and prevents memory leaks
or resource exhaustion during long-running batch operations.
"""

import os
import gc
import shutil
import logging
import weakref
from typing import Dict, List, Optional, Set, Any
from datetime import datetime, timedelta
from pathlib import Path
import json
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass, field
import threading

logger = logging.getLogger(__name__)


@dataclass
class ResourceStats:
    """Track resource usage statistics."""
    temp_files_created: int = 0
    temp_files_cleaned: int = 0
    temp_space_used_mb: float = 0.0
    peak_temp_space_mb: float = 0.0
    db_connections_created: int = 0
    db_connections_reused: int = 0
    credentials_cached: int = 0
    credentials_cache_hits: int = 0
    large_files_processed: int = 0
    memory_cleanups_triggered: int = 0


class ResourceManager:
    """
    Comprehensive resource manager for book ingestion operations.
    
    Handles:
    - Temporary file lifecycle management
    - Database connection pooling
    - Google Drive credential caching
    - Memory management for large files
    - Resource usage monitoring
    """
    
    # Configuration constants
    TEMP_DIR_PREFIX = "book_ingestion_"
    CREDENTIAL_CACHE_TTL = timedelta(hours=1)
    LARGE_FILE_THRESHOLD_MB = 10
    MAX_TEMP_SPACE_MB = 1000  # 1GB limit for temp files
    DB_CONNECTION_POOL_SIZE = 5
    
    def __init__(self, job_id: str, base_temp_dir: Optional[str] = None):
        """
        Initialize resource manager.
        
        Args:
            job_id: Unique job identifier
            base_temp_dir: Base directory for temporary files (defaults to system temp)
        """
        self.job_id = job_id
        self.stats = ResourceStats()
        
        # Create job-specific temp directory
        if base_temp_dir:
            self.base_temp_dir = Path(base_temp_dir)
        else:
            self.base_temp_dir = Path(tempfile.gettempdir())
        
        self.job_temp_dir = self.base_temp_dir / f"{self.TEMP_DIR_PREFIX}{job_id}"
        self.job_temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Resource tracking
        self.temp_files: Set[Path] = set()
        self.active_connections: Dict[str, Any] = {}
        self.credential_cache: Dict[str, Dict[str, Any]] = {}
        self.large_file_paths: Set[str] = set()  # Track paths as strings instead
        
        # Thread safety
        self._lock = threading.Lock()
        
        logger.info(f"ResourceManager initialized for job {job_id}, temp dir: {self.job_temp_dir}")
    
    @contextmanager
    def temp_file(self, suffix: str = "", prefix: str = "page_", 
                  cleanup_on_exit: bool = True) -> Path:
        """
        Context manager for temporary file creation and cleanup.
        
        Args:
            suffix: File suffix (e.g., '.png')
            prefix: File prefix
            cleanup_on_exit: Whether to cleanup on context exit
            
        Yields:
            Path to temporary file
        """
        temp_path = None
        try:
            # Create temp file in job directory
            with tempfile.NamedTemporaryFile(
                mode='wb',
                suffix=suffix,
                prefix=prefix,
                dir=self.job_temp_dir,
                delete=False
            ) as tf:
                temp_path = Path(tf.name)
            
            # Track the file
            with self._lock:
                self.temp_files.add(temp_path)
                self.stats.temp_files_created += 1
                self._update_temp_space_stats()
            
            logger.debug(f"Created temp file: {temp_path}")
            yield temp_path
            
        finally:
            if cleanup_on_exit and temp_path:
                self.cleanup_file(temp_path)
    
    def cleanup_file(self, file_path: Path) -> bool:
        """
        Clean up a specific file.
        
        Args:
            file_path: Path to file to clean up
            
        Returns:
            True if cleanup successful
        """
        try:
            if file_path.exists():
                file_path.unlink()
                
            with self._lock:
                self.temp_files.discard(file_path)
                self.stats.temp_files_cleaned += 1
                self._update_temp_space_stats()
            
            logger.debug(f"Cleaned up file: {file_path}")
            return True
            
        except Exception as e:
            logger.warning(f"Failed to cleanup file {file_path}: {e}")
            return False
    
    def cleanup_page_resources(self, page_number: int) -> None:
        """
        Clean up all resources for a specific page.
        
        Args:
            page_number: Page number to clean up
        """
        logger.debug(f"Cleaning up resources for page {page_number}")
        
        # Find and clean up page-specific files
        with self._lock:
            page_files = [
                f for f in self.temp_files 
                if f"page_{page_number}_" in f.name or f"_p{page_number}." in f.name
            ]
        
        for file_path in page_files:
            self.cleanup_file(file_path)
        
        # Trigger garbage collection for large files
        if self.stats.large_files_processed > 0:
            gc.collect()
            self.stats.memory_cleanups_triggered += 1
    
    def get_db_connection(self, connection_key: str, 
                         connection_factory: callable) -> Any:
        """
        Get or create a database connection with pooling.
        
        Args:
            connection_key: Unique key for this connection type
            connection_factory: Callable that creates a new connection
            
        Returns:
            Database connection object
        """
        with self._lock:
            if connection_key in self.active_connections:
                # Reuse existing connection
                conn = self.active_connections[connection_key]
                self.stats.db_connections_reused += 1
                logger.debug(f"Reusing DB connection: {connection_key}")
                return conn
            
            # Create new connection
            conn = connection_factory()
            self.active_connections[connection_key] = conn
            self.stats.db_connections_created += 1
            logger.debug(f"Created new DB connection: {connection_key}")
            return conn
    
    def close_db_connections(self) -> None:
        """Close all active database connections."""
        with self._lock:
            for key, conn in self.active_connections.items():
                try:
                    if hasattr(conn, 'close'):
                        conn.close()
                    logger.debug(f"Closed DB connection: {key}")
                except Exception as e:
                    logger.warning(f"Error closing DB connection {key}: {e}")
            
            self.active_connections.clear()
    
    def cache_credentials(self, client_user_id: str, 
                         credentials: Dict[str, Any]) -> None:
        """
        Cache Google Drive credentials for a client.
        
        Args:
            client_user_id: Client user ID
            credentials: Credential data to cache
        """
        with self._lock:
            self.credential_cache[client_user_id] = {
                'credentials': credentials,
                'cached_at': datetime.now(),
                'expires_at': datetime.now() + self.CREDENTIAL_CACHE_TTL
            }
            self.stats.credentials_cached += 1
        
        logger.debug(f"Cached credentials for client: {client_user_id}")
    
    def get_cached_credentials(self, client_user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get cached credentials for a client.
        
        Args:
            client_user_id: Client user ID
            
        Returns:
            Cached credentials or None if not found/expired
        """
        with self._lock:
            if client_user_id not in self.credential_cache:
                return None
            
            cache_entry = self.credential_cache[client_user_id]
            
            # Check if expired
            if datetime.now() > cache_entry['expires_at']:
                del self.credential_cache[client_user_id]
                logger.debug(f"Credentials expired for client: {client_user_id}")
                return None
            
            self.stats.credentials_cache_hits += 1
            logger.debug(f"Retrieved cached credentials for client: {client_user_id}")
            return cache_entry['credentials']
    
    def track_large_file(self, file_path: Path) -> None:
        """
        Track a large file for memory management.
        
        Args:
            file_path: Path to large file
        """
        try:
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            
            if file_size_mb > self.LARGE_FILE_THRESHOLD_MB:
                with self._lock:
                    self.large_file_paths.add(str(file_path))
                    self.stats.large_files_processed += 1
                
                logger.info(f"Tracking large file ({file_size_mb:.1f}MB): {file_path.name}")
        except Exception as e:
            logger.warning(f"Error tracking large file {file_path}: {e}")
    
    def _update_temp_space_stats(self) -> None:
        """Update temporary space usage statistics."""
        try:
            total_size = sum(
                f.stat().st_size for f in self.temp_files if f.exists()
            )
            self.stats.temp_space_used_mb = total_size / (1024 * 1024)
            self.stats.peak_temp_space_mb = max(
                self.stats.peak_temp_space_mb,
                self.stats.temp_space_used_mb
            )
            
            # Warn if approaching limit
            if self.stats.temp_space_used_mb > self.MAX_TEMP_SPACE_MB * 0.8:
                logger.warning(
                    f"Temp space usage high: {self.stats.temp_space_used_mb:.1f}MB "
                    f"(limit: {self.MAX_TEMP_SPACE_MB}MB)"
                )
        except Exception as e:
            logger.debug(f"Error updating temp space stats: {e}")
    
    def get_resource_stats(self) -> Dict[str, Any]:
        """Get current resource usage statistics."""
        with self._lock:
            return {
                "job_id": self.job_id,
                "temp_files": {
                    "created": self.stats.temp_files_created,
                    "cleaned": self.stats.temp_files_cleaned,
                    "active": len(self.temp_files),
                    "space_used_mb": f"{self.stats.temp_space_used_mb:.1f}",
                    "peak_space_mb": f"{self.stats.peak_temp_space_mb:.1f}"
                },
                "database": {
                    "connections_created": self.stats.db_connections_created,
                    "connections_reused": self.stats.db_connections_reused,
                    "active_connections": len(self.active_connections)
                },
                "credentials": {
                    "cached": self.stats.credentials_cached,
                    "cache_hits": self.stats.credentials_cache_hits,
                    "active_cache_entries": len(self.credential_cache)
                },
                "memory": {
                    "large_files_processed": self.stats.large_files_processed,
                    "memory_cleanups": self.stats.memory_cleanups_triggered
                }
            }
    
    def cleanup_all(self) -> None:
        """Clean up all resources managed by this instance."""
        logger.info(f"Starting full cleanup for job {self.job_id}")
        
        # Close database connections
        self.close_db_connections()
        
        # Clean up all temp files
        with self._lock:
            temp_files_copy = list(self.temp_files)
        
        for file_path in temp_files_copy:
            self.cleanup_file(file_path)
        
        # Remove job temp directory
        try:
            if self.job_temp_dir.exists():
                shutil.rmtree(self.job_temp_dir)
                logger.info(f"Removed job temp directory: {self.job_temp_dir}")
        except Exception as e:
            logger.warning(f"Error removing job temp directory: {e}")
        
        # Clear caches
        with self._lock:
            self.credential_cache.clear()
            self.large_file_paths.clear()
        
        # Force garbage collection
        gc.collect()
        
        # Log final stats
        logger.info(f"Cleanup complete. Final stats: {self.get_resource_stats()}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup all resources."""
        self.cleanup_all()