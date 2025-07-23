#!/usr/bin/env python3
"""
Run all unit tests for the book ingestion crew.

This script runs all test modules and provides a summary of results.
"""
import sys
import pytest
from pathlib import Path

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))


def run_all_tests():
    """Run all test modules and return exit code."""
    test_modules = [
        "test_google_drive_download_tool.py",
        "test_image_viewer_tool.py", 
        "test_sync_db_storage_tool.py",
        "test_schema_validation.py",
        "test_error_handling.py"
    ]
    
    # Run pytest with verbose output and coverage
    args = [
        "-v",  # Verbose
        "-s",  # No capture (show print statements)
        "--tb=short",  # Short traceback format
        "--color=yes",  # Colored output
    ]
    
    # Add coverage if available
    try:
        import pytest_cov
        args.extend([
            "--cov=crews.book_ingestion_crew",
            "--cov=tools",
            "--cov-report=term-missing",
            "--cov-report=html:coverage_report"
        ])
    except ImportError:
        print("Note: Install pytest-cov for coverage reports")
    
    # Add test files
    test_dir = Path(__file__).parent
    for module in test_modules:
        test_file = test_dir / module
        if test_file.exists():
            args.append(str(test_file))
    
    # Run tests
    print("=" * 80)
    print("Running Book Ingestion Crew Unit Tests")
    print("=" * 80)
    
    exit_code = pytest.main(args)
    
    if exit_code == 0:
        print("\n" + "=" * 80)
        print("✅ All tests passed!")
        print("=" * 80)
    else:
        print("\n" + "=" * 80)
        print("❌ Some tests failed. See output above.")
        print("=" * 80)
    
    return exit_code


if __name__ == "__main__":
    sys.exit(run_all_tests())