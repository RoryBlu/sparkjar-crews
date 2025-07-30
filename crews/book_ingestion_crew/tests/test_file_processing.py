#!/usr/bin/env python3
"""
Test script for file processing utilities.

Demonstrates the enhanced filename parsing and sorting capabilities.
"""

from file_processing_utils import (
    FilenameParser,
    create_file_parser,
    sort_files_by_page_number,
    validate_page_sequence
)


def test_various_formats():
    """Test parsing of various filename formats."""
    
    # Create test files with different naming conventions
    test_files = [
        # Baron format (existing)
        {"name": "baron001.png", "id": "1"},
        {"name": "baron001 1.png", "id": "2"},
        {"name": "baron001 24.png", "id": "3"},
        {"name": "baron002.png", "id": "4"},
        {"name": "baron002 24.png", "id": "5"},
        
        # Numeric formats
        {"name": "001.jpg", "id": "6"},
        {"name": "002.jpg", "id": "7"},
        {"name": "010.jpg", "id": "8"},
        {"name": "0100.png", "id": "9"},
        
        # Page prefixed
        {"name": "page001.png", "id": "10"},
        {"name": "page_002.png", "id": "11"},
        {"name": "page-010.png", "id": "12"},
        {"name": "p015.png", "id": "13"},
        {"name": "pg020.png", "id": "14"},
        
        # Chapter and page
        {"name": "chapter1_page001.png", "id": "15"},
        {"name": "chapter2_page001.png", "id": "16"},
        {"name": "ch01_p010.png", "id": "17"},
        
        # Image/scan prefixed
        {"name": "image001.png", "id": "18"},
        {"name": "scan002.jpg", "id": "19"},
        {"name": "img100.png", "id": "20"},
        
        # Book pages
        {"name": "book_page_001.png", "id": "21"},
        {"name": "book-p002.png", "id": "22"},
        
        # Complex names
        {"name": "manuscript_001.png", "id": "23"},
        {"name": "document_2023_015.jpg", "id": "24"},
        
        # Edge cases
        {"name": "no_numbers_here.png", "id": "25"},
        {"name": "page.png", "id": "26"},
        {"name": "2023_report_page_042.pdf", "id": "27"},
    ]
    
    # Create parser
    parser = create_file_parser()
    
    # Sort files
    sorted_files = sort_files_by_page_number(test_files, parser)
    
    # Print results
    print("File Processing Test Results")
    print("=" * 100)
    print(f"{'Original Name':<35} {'Page #':<8} {'Format':<15} {'Confidence':<12} {'Notes'}")
    print("-" * 100)
    
    for file in sorted_files:
        page_info = file.get('page_info', {})
        notes = ""
        
        # Add notes for special cases
        if file.get('filename_format') == 'baron':
            metadata = page_info.get('metadata', {})
            notes = f"Group {metadata.get('group')}, Pos {metadata.get('position')}"
        elif file.get('filename_format') == 'named':
            metadata = page_info.get('metadata', {})
            if 'chapter' in metadata:
                notes = f"Chapter {metadata.get('chapter')}"
        elif file.get('filename_format') == 'unknown':
            notes = "⚠️  Low confidence"
        
        print(f"{file['name']:<35} {file['calculated_page_number']:<8} "
              f"{file.get('filename_format', 'unknown'):<15} "
              f"{file.get('page_confidence', 0):<12.2f} {notes}")
    
    # Validate sequence
    print("\n" + "=" * 100)
    print("Page Sequence Validation")
    print("-" * 100)
    
    issues = validate_page_sequence(sorted_files, max_gap=10)
    
    if not issues:
        print("✅ No issues found in page sequence")
    else:
        for issue in issues:
            severity_emoji = {
                'error': '❌',
                'warning': '⚠️',
                'info': 'ℹ️'
            }.get(issue['severity'], '•')
            
            print(f"{severity_emoji} {issue['type']}: {issue['message']}")
            if 'files' in issue and len(issue['files']) <= 5:
                for f in issue['files']:
                    print(f"   - {f}")
    
    print("\n" + "=" * 100)
    print("Summary:")
    print(f"Total files: {len(test_files)}")
    print(f"Successfully parsed: {sum(1 for f in sorted_files if f.get('page_confidence', 0) > 0)}")
    print(f"Low confidence: {sum(1 for f in sorted_files if f.get('page_confidence', 0) < 0.5)}")
    print(f"Unknown format: {sum(1 for f in sorted_files if f.get('filename_format') == 'unknown')}")


def test_custom_patterns():
    """Test with custom filename patterns."""
    
    print("\n" + "=" * 100)
    print("Testing Custom Patterns")
    print("-" * 100)
    
    # Define custom pattern for a specific format
    # Example: "ABC_2023_12_25_p001.jpg" format
    custom_patterns = {
        'custom_date_format': re.compile(r'[A-Z]+_\d{4}_\d{2}_\d{2}_p(\d+)', re.IGNORECASE)
    }
    
    # Create parser with custom patterns
    import re
    parser = FilenameParser(custom_patterns)
    
    # Override parse method to handle custom format
    original_parse = parser.parse
    
    def parse_with_custom(filename):
        # Try custom pattern first
        name_without_ext = filename.rsplit('.', 1)[0]
        match = parser.patterns['custom_date_format'].match(name_without_ext)
        
        if match:
            from file_processing_utils import PageInfo, FilenameFormat
            return PageInfo(
                filename=filename,
                page_number=int(match.group(1)),
                format_type=FilenameFormat.CUSTOM,
                confidence=0.95,
                metadata={'pattern': 'custom_date_format'}
            )
        
        # Fall back to original parsing
        return original_parse(filename)
    
    parser.parse = parse_with_custom
    
    # Test files with custom format
    test_files = [
        {"name": "ABC_2023_12_25_p001.jpg"},
        {"name": "XYZ_2024_01_15_p042.png"},
        {"name": "DOC_2023_11_30_p100.pdf"},
    ]
    
    sorted_files = sort_files_by_page_number(test_files, parser)
    
    for file in sorted_files:
        print(f"{file['name']:<35} Page {file['calculated_page_number']:<4} "
              f"(Format: {file.get('filename_format')})")


if __name__ == "__main__":
    test_various_formats()
    test_custom_patterns()