"""
Comprehensive file sorting and page number extraction utilities for book ingestion.

This module implements task 9 requirements:
- Filename parsing to extract page numbers
- File sorting logic to process pages in correct order
- Support for various filename formats
- Edge case handling in filename parsing

Requirements: 5.3, 6.1
"""
import re
import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class FilenameFormat(Enum):
    """Supported filename formats for page number extraction."""
    BARON = "baron"           # baron001.png, baron001 24.png
    NUMERIC = "numeric"       # 001.png, 0001.jpg, page001.png
    PREFIXED = "prefixed"     # page_001.png, p001.png, pg001.png
    NAMED = "named"           # chapter1_page001.png, book_page_001.png
    SEQUENTIAL = "sequential" # image001.png, scan001.png, img001.png
    CUSTOM = "custom"         # User-defined pattern
    UNKNOWN = "unknown"       # Cannot determine format


@dataclass
class PageInfo:
    """Structured information extracted from a filename."""
    filename: str
    page_number: int
    format_type: FilenameFormat
    confidence: float  # 0.0 to 1.0 confidence in the extraction
    metadata: Dict[str, Any]  # Format-specific metadata
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'filename': self.filename,
            'page_number': self.page_number,
            'format_type': self.format_type.value,
            'confidence': self.confidence,
            'metadata': self.metadata
        }


class FilenameParser:
    """
    Comprehensive filename parser supporting multiple formats.
    
    Handles various naming conventions and edge cases for manuscript page files.
    """
    
    # Common page number patterns
    PATTERNS = {
        # Baron format: baron001.png, baron001 24.png
        'baron': re.compile(r'baron(\d{3})(?:\s+(\d+))?', re.IGNORECASE),
        
        # Simple numeric: 001.png, 0001.jpg
        'numeric_only': re.compile(r'^(\d+)\.', re.IGNORECASE),
        
        # Page prefix: page001.png, page_001.png, page-001.png
        'page_prefix': re.compile(r'page[\s_-]*(\d+)', re.IGNORECASE),
        
        # Short prefix: p001.png, pg001.png
        'short_prefix': re.compile(r'^p(?:g)?[\s_-]*(\d+)', re.IGNORECASE),
        
        # Chapter and page: chapter1_page001.png, ch01_p001.png
        'chapter_page': re.compile(r'ch(?:apter)?[\s_-]*(\d+)[\s_-]*p(?:age)?[\s_-]*(\d+)', re.IGNORECASE),
        
        # Image/scan prefix: image001.png, scan001.png, img001.png
        'image_prefix': re.compile(r'(?:image|scan|img)[\s_-]*(\d+)', re.IGNORECASE),
        
        # Book page: book_page_001.png, book-p001.png
        'book_page': re.compile(r'book[\s_-]*p(?:age)?[\s_-]*(\d+)', re.IGNORECASE),
        
        # Numbered with text: manuscript_001.png, document_001.png
        'text_number': re.compile(r'[a-zA-Z]+[\s_-]+(\d+)'),
        
        # Range format: pages_001-025.png (for multi-page files)
        'range': re.compile(r'(\d+)[\s_-]*(?:to|-)[\s_-]*(\d+)', re.IGNORECASE),
    }
    
    def __init__(self, custom_patterns: Optional[Dict[str, re.Pattern]] = None):
        """
        Initialize parser with optional custom patterns.
        
        Args:
            custom_patterns: Dictionary of custom regex patterns for specific formats
        """
        self.patterns = self.PATTERNS.copy()
        if custom_patterns:
            self.patterns.update(custom_patterns)
    
    def parse_baron_format(self, filename: str) -> Optional[PageInfo]:
        """Parse baron-specific filename format."""
        name_without_ext = filename.rsplit('.', 1)[0]
        match = self.patterns['baron'].match(name_without_ext)
        
        if not match:
            return None
        
        group_str = match.group(1)
        position_str = match.group(2)
        
        # Convert group to int
        group = int(group_str)
        
        # Position: if no suffix, it's position 1
        # if suffix exists, position = suffix + 1
        if position_str is None:
            position = 1
        else:
            position = int(position_str) + 1
        
        # Calculate page number: (group - 1) * 25 + position
        page_number = (group - 1) * 25 + position
        
        return PageInfo(
            filename=filename,
            page_number=page_number,
            format_type=FilenameFormat.BARON,
            confidence=1.0,  # High confidence for exact match
            metadata={
                'group': group,
                'position': position,
                'group_str': group_str,
                'position_str': position_str or ''
            }
        )
    
    def parse_numeric_format(self, filename: str) -> Optional[PageInfo]:
        """Parse simple numeric filename format."""
        match = self.patterns['numeric_only'].match(filename)
        
        if not match:
            return None
        
        page_number = int(match.group(1))
        
        return PageInfo(
            filename=filename,
            page_number=page_number,
            format_type=FilenameFormat.NUMERIC,
            confidence=0.9,  # High confidence
            metadata={'raw_number': match.group(1)}
        )
    
    def parse_prefixed_format(self, filename: str) -> Optional[PageInfo]:
        """Parse various prefixed filename formats."""
        name_without_ext = filename.rsplit('.', 1)[0]
        
        # Try different prefix patterns
        for pattern_name, pattern in [
            ('page_prefix', self.patterns['page_prefix']),
            ('short_prefix', self.patterns['short_prefix']),
            ('image_prefix', self.patterns['image_prefix']),
            ('book_page', self.patterns['book_page']),
        ]:
            match = pattern.search(name_without_ext)
            if match:
                page_number = int(match.group(1))
                
                return PageInfo(
                    filename=filename,
                    page_number=page_number,
                    format_type=FilenameFormat.PREFIXED,
                    confidence=0.85,
                    metadata={
                        'pattern': pattern_name,
                        'raw_number': match.group(1)
                    }
                )
        
        return None
    
    def parse_chapter_page_format(self, filename: str) -> Optional[PageInfo]:
        """Parse chapter and page format."""
        name_without_ext = filename.rsplit('.', 1)[0]
        match = self.patterns['chapter_page'].search(name_without_ext)
        
        if not match:
            return None
        
        chapter = int(match.group(1))
        page_in_chapter = int(match.group(2))
        
        # Assume 50 pages per chapter as default
        # This can be customized based on specific book structure
        pages_per_chapter = 50
        page_number = (chapter - 1) * pages_per_chapter + page_in_chapter
        
        return PageInfo(
            filename=filename,
            page_number=page_number,
            format_type=FilenameFormat.NAMED,
            confidence=0.7,  # Lower confidence due to assumption
            metadata={
                'chapter': chapter,
                'page_in_chapter': page_in_chapter,
                'assumed_pages_per_chapter': pages_per_chapter
            }
        )
    
    def parse_text_number_format(self, filename: str) -> Optional[PageInfo]:
        """Parse text followed by number format."""
        name_without_ext = filename.rsplit('.', 1)[0]
        match = self.patterns['text_number'].search(name_without_ext)
        
        if not match:
            return None
        
        page_number = int(match.group(1))
        
        return PageInfo(
            filename=filename,
            page_number=page_number,
            format_type=FilenameFormat.SEQUENTIAL,
            confidence=0.75,
            metadata={'raw_number': match.group(1)}
        )
    
    def extract_any_number(self, filename: str) -> Optional[PageInfo]:
        """
        Fallback: Extract any number from the filename.
        
        Used when no specific format matches.
        """
        # Remove extension
        name_without_ext = filename.rsplit('.', 1)[0]
        
        # Find all numbers in the filename
        numbers = re.findall(r'\d+', name_without_ext)
        
        if not numbers:
            return None
        
        # Heuristics for choosing the right number:
        # 1. Prefer 3-4 digit numbers (likely page numbers)
        # 2. Prefer numbers at the end of the filename
        # 3. Prefer larger numbers if multiple exist
        
        candidate_numbers = []
        for num_str in numbers:
            num = int(num_str)
            # Score based on position (later = better)
            position_score = name_without_ext.rfind(num_str) / len(name_without_ext)
            # Score based on digit count (3-4 digits = best)
            digit_score = 1.0 if 3 <= len(num_str) <= 4 else 0.5
            # Combined score
            score = position_score * 0.7 + digit_score * 0.3
            candidate_numbers.append((num, score, num_str))
        
        # Sort by score (descending)
        candidate_numbers.sort(key=lambda x: x[1], reverse=True)
        
        if candidate_numbers:
            page_number, score, raw_number = candidate_numbers[0]
            
            return PageInfo(
                filename=filename,
                page_number=page_number,
                format_type=FilenameFormat.UNKNOWN,
                confidence=min(0.5, score),  # Low confidence for fallback
                metadata={
                    'extraction_method': 'fallback',
                    'raw_number': raw_number,
                    'all_numbers': numbers
                }
            )
        
        return None
    
    def parse(self, filename: str) -> PageInfo:
        """
        Parse a filename to extract page information.
        
        Tries multiple parsing strategies in order of specificity.
        
        Args:
            filename: The filename to parse
            
        Returns:
            PageInfo object with extracted information
        """
        # Try parsing strategies in order of specificity
        parsing_strategies = [
            self.parse_baron_format,
            self.parse_numeric_format,
            self.parse_prefixed_format,
            self.parse_chapter_page_format,
            self.parse_text_number_format,
            self.extract_any_number,
        ]
        
        for strategy in parsing_strategies:
            try:
                result = strategy(filename)
                if result:
                    logger.debug(f"Parsed '{filename}' using {strategy.__name__}: page {result.page_number}")
                    return result
            except Exception as e:
                logger.warning(f"Error in {strategy.__name__} for '{filename}': {e}")
                continue
        
        # If all strategies fail, return a default
        logger.warning(f"Could not parse page number from '{filename}', assigning page 9999")
        return PageInfo(
            filename=filename,
            page_number=9999,  # Sort to end
            format_type=FilenameFormat.UNKNOWN,
            confidence=0.0,
            metadata={'error': 'No page number found'}
        )


def create_file_parser(custom_patterns: Optional[Dict[str, re.Pattern]] = None) -> FilenameParser:
    """
    Factory function to create a FilenameParser instance.
    
    Args:
        custom_patterns: Optional custom regex patterns
        
    Returns:
        Configured FilenameParser
    """
    return FilenameParser(custom_patterns)


def sort_files_by_page_number(
    files: List[Dict[str, Any]], 
    parser: Optional[FilenameParser] = None,
    filename_field: str = 'name'
) -> List[Dict[str, Any]]:
    """
    Sort files by their extracted page numbers.
    
    Args:
        files: List of file dictionaries
        parser: Optional custom parser (uses default if not provided)
        filename_field: Field name containing the filename (default: 'name')
        
    Returns:
        Sorted list of files with added page information
    """
    if parser is None:
        parser = FilenameParser()
    
    # Process each file
    processed_files = []
    for file in files:
        # Get filename from the specified field
        filename = file.get(filename_field) or file.get('file_name') or file.get('name')
        
        if not filename:
            logger.warning(f"No filename found in file dict: {file}")
            # Add to end of list
            file['page_info'] = None
            file['calculated_page_number'] = 9999
            processed_files.append(file)
            continue
        
        # Parse the filename
        page_info = parser.parse(filename)
        
        # Add page information to file dict
        file['page_info'] = page_info.to_dict()
        file['calculated_page_number'] = page_info.page_number
        file['page_confidence'] = page_info.confidence
        file['filename_format'] = page_info.format_type.value
        
        # Ensure consistent filename fields
        file['file_name'] = filename
        file['name'] = filename
        
        processed_files.append(file)
    
    # Sort by page number, then by confidence (for ties)
    sorted_files = sorted(
        processed_files, 
        key=lambda x: (x['calculated_page_number'], -x.get('page_confidence', 0))
    )
    
    # Log sorting summary
    logger.info(f"Sorted {len(sorted_files)} files by page number")
    if sorted_files:
        logger.info(f"First page: {sorted_files[0].get('file_name')} (page {sorted_files[0].get('calculated_page_number')})")
        logger.info(f"Last page: {sorted_files[-1].get('file_name')} (page {sorted_files[-1].get('calculated_page_number')})")
    
    return sorted_files


def validate_page_sequence(sorted_files: List[Dict[str, Any]], max_gap: int = 5) -> List[Dict[str, Any]]:
    """
    Validate the page sequence and identify potential issues.
    
    Args:
        sorted_files: List of sorted files with page numbers
        max_gap: Maximum allowed gap between consecutive pages
        
    Returns:
        List of validation issues found
    """
    issues = []
    
    if not sorted_files:
        return issues
    
    # Check for gaps in page numbering
    prev_page = sorted_files[0].get('calculated_page_number', 0)
    
    for i, file in enumerate(sorted_files[1:], 1):
        current_page = file.get('calculated_page_number', 0)
        gap = current_page - prev_page
        
        if gap > max_gap:
            issues.append({
                'type': 'large_gap',
                'severity': 'warning',
                'message': f"Large gap between pages {prev_page} and {current_page}",
                'files': [sorted_files[i-1].get('file_name'), file.get('file_name')],
                'gap_size': gap
            })
        elif gap < 0:
            issues.append({
                'type': 'negative_gap',
                'severity': 'error',
                'message': f"Page numbers out of order: {prev_page} followed by {current_page}",
                'files': [sorted_files[i-1].get('file_name'), file.get('file_name')]
            })
        elif gap == 0:
            issues.append({
                'type': 'duplicate_page',
                'severity': 'warning',
                'message': f"Duplicate page number: {current_page}",
                'files': [sorted_files[i-1].get('file_name'), file.get('file_name')]
            })
        
        prev_page = current_page
    
    # Check for low confidence extractions
    low_confidence_files = [
        f for f in sorted_files 
        if f.get('page_confidence', 1.0) < 0.5
    ]
    
    if low_confidence_files:
        issues.append({
            'type': 'low_confidence',
            'severity': 'info',
            'message': f"{len(low_confidence_files)} files with low confidence page extraction",
            'files': [f.get('file_name') for f in low_confidence_files[:5]],  # First 5
            'total_count': len(low_confidence_files)
        })
    
    return issues


# Backward compatibility functions
def parse_baron_filename(filename: str) -> Dict[str, Any]:
    """
    Backward compatibility wrapper for baron filename parsing.
    
    Maintains the original function signature for existing code.
    """
    parser = FilenameParser()
    result = parser.parse_baron_format(filename)
    
    if result:
        return {
            'filename': result.filename,
            'page_number': result.page_number,
            'group': result.metadata.get('group'),
            'position': result.metadata.get('position'),
            'group_str': result.metadata.get('group_str'),
            'position_str': result.metadata.get('position_str')
        }
    else:
        raise ValueError(f"Filename '{filename}' doesn't match baron pattern")


def sort_book_files(files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Backward compatibility wrapper for file sorting.
    
    Maintains the original function signature for existing code.
    """
    return sort_files_by_page_number(files)


# Test utilities
if __name__ == "__main__":
    # Test various filename formats
    test_files = [
        # Baron format
        "baron001.png",
        "baron001 1.png",
        "baron001 24.png",
        "baron002.png",
        
        # Numeric formats
        "001.jpg",
        "0001.png",
        "123.tiff",
        
        # Prefixed formats
        "page001.png",
        "page_001.jpg",
        "page-001.png",
        "p001.png",
        "pg001.png",
        
        # Chapter formats
        "chapter1_page001.png",
        "ch01_p001.png",
        
        # Image formats
        "image001.png",
        "scan001.jpg",
        "img001.png",
        
        # Complex formats
        "manuscript_001.png",
        "book_page_001.png",
        "document_2023_001.jpg",
        
        # Edge cases
        "no_number_here.png",
        "multiple_123_456.png",
        "page.png",
    ]
    
    parser = FilenameParser()
    
    print("Testing filename parser:")
    print("-" * 80)
    print(f"{'Filename':<30} {'Page':<6} {'Format':<12} {'Confidence':<10}")
    print("-" * 80)
    
    for filename in test_files:
        info = parser.parse(filename)
        print(f"{filename:<30} {info.page_number:<6} {info.format_type.value:<12} {info.confidence:<10.2f}")
    
    # Test sorting
    print("\n" + "=" * 80)
    print("Testing file sorting:")
    print("-" * 80)
    
    file_dicts = [{'name': f} for f in test_files]
    sorted_files = sort_files_by_page_number(file_dicts)
    
    for file in sorted_files[:10]:  # Show first 10
        print(f"Page {file['calculated_page_number']:4d}: {file['name']:<30} "
              f"(confidence: {file['page_confidence']:.2f})")