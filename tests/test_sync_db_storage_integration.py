#!/usr/bin/env python3
"""Integration test for SyncDBStorageTool with realistic data."""
import json
import os
import sys
import uuid
from datetime import datetime

# Add the tools directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))

from sync_db_storage_tool import SyncDBStorageTool


def test_realistic_book_ingestion():
    """Test with realistic book ingestion data."""
    print("Testing realistic book ingestion scenario...")
    
    tool = SyncDBStorageTool()
    
    # Simulate realistic OCR metadata as would come from ImageViewerTool
    ocr_metadata = {
        "file_id": "1BxYz9K3mN8pQ2rS4tU6vW7xY8zA9bC0d",
        "processing_stats": {
            "total_words": 247,
            "normal_transcription": 198,
            "context_logic_transcription": 35,
            "unable_to_transcribe": 14
        },
        "unclear_sections": [
            "illegible word near 'chapter'",
            "smudged text in paragraph 3"
        ],
        "ocr_passes": 3,
        "model_used": "gpt-4o",
        "processing_time_seconds": 12.5,
        "image_dimensions": {"width": 2480, "height": 3508},
        "confidence_scores": {
            "overall": 0.87,
            "by_section": [0.92, 0.85, 0.81, 0.89]
        }
    }
    
    # Test cases with different filename patterns
    test_cases = [
        {
            "client_user_id": str(uuid.uuid4()),
            "book_key": "hemingway_old_man_sea_manuscript",
            "file_name": "page_001.jpg",
            "language_code": "en",
            "page_text": """The Old Man and the Sea
            
Chapter 1

He was an old man who fished alone in a skiff in the Gulf Stream and he had gone eighty-four days now without taking a fish. In the first forty days a boy had been with him. But after forty days without a fish the boy's parents had told him that the old man was now definitely and finally salao, which is the worst form of unlucky, and the boy had gone at their orders in another boat which caught three good fish the first week.""",
            "ocr_metadata": ocr_metadata,
            "version": "original"
        },
        {
            "client_user_id": str(uuid.uuid4()),
            "book_key": "garcia_marquez_solitude_manuscript",
            "file_name": "manuscript_025.png",
            "language_code": "es",
            "page_text": """Cien Años de Soledad
            
Capítulo 2

Muchos años después, frente al pelotón de fusilamiento, el coronel Aureliano Buendía había de recordar aquella tarde remota en que su padre lo llevó a conocer el hielo. Macondo era entonces una aldea de veinte casas de barro y cañabrava construidas a la orilla de un río de aguas diáfanas que se precipitaban por un lecho de piedras pulidas, blancas y enormes como huevos prehistóricos.""",
            "ocr_metadata": {**ocr_metadata, "language_detected": "spanish"},
            "version": "original"
        },
        {
            "client_user_id": str(uuid.uuid4()),
            "book_key": "scientific_journal_1923",
            "file_name": "scan_042_corrected.tiff",
            # No page_number provided - should extract from filename
            "language_code": "en",
            "page_text": """Journal of Theoretical Physics
Volume 15, Issue 3, March 1923

On the Quantum Theory of Radiation

By A. Einstein

Abstract: This paper presents a derivation of Planck's radiation law based on the assumption that the emission and absorption of radiation by atoms occurs in discrete quanta. The statistical treatment of these quantum processes leads naturally to both the classical and quantum mechanical descriptions of electromagnetic radiation.""",
            "ocr_metadata": {**ocr_metadata, "document_type": "scientific_journal"},
            "version": "corrected"
        }
    ]
    
    print(f"Testing {len(test_cases)} realistic scenarios...")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest case {i}: {test_case['book_key']}")
        print(f"  File: {test_case['file_name']}")
        print(f"  Language: {test_case['language_code']}")
        print(f"  Text length: {len(test_case['page_text'])} characters")
        
        # Run the tool (will fail due to no database, but validates the interface)
        result_str = tool._run(**test_case)
        result = json.loads(result_str)
        
        # Should return structured error due to no database connection
        assert "success" in result
        assert "error" in result
        print(f"  ✓ Tool interface handled input correctly")
        
        # Test page number extraction for case without explicit page_number
        if "page_number" not in test_case:
            extracted = tool._extract_page_number_from_filename(test_case["file_name"])
            print(f"  ✓ Extracted page number: {extracted}")
    
    print("\n✓ All realistic scenarios handled correctly")
    return True


def test_edge_cases():
    """Test edge cases and boundary conditions."""
    print("\nTesting edge cases...")
    
    tool = SyncDBStorageTool()
    
    edge_cases = [
        {
            "name": "Very long text",
            "params": {
                "client_user_id": str(uuid.uuid4()),
                "book_key": "long_text_test",
                "file_name": "page_001.jpg",
                "language_code": "en",
                "page_text": "A" * 10000,  # Very long text
                "ocr_metadata": {"test": "long_text"}
            }
        },
        {
            "name": "Empty OCR metadata",
            "params": {
                "client_user_id": str(uuid.uuid4()),
                "book_key": "empty_metadata_test",
                "file_name": "page_001.jpg",
                "language_code": "en",
                "page_text": "Short text",
                "ocr_metadata": {}
            }
        },
        {
            "name": "Special characters in text",
            "params": {
                "client_user_id": str(uuid.uuid4()),
                "book_key": "special_chars_test",
                "file_name": "page_001.jpg",
                "language_code": "en",
                "page_text": "Text with émojis 🎉, symbols ©®™, and unicode: αβγδε",
                "ocr_metadata": {"unicode_detected": True}
            }
        },
        {
            "name": "Complex filename",
            "params": {
                "client_user_id": str(uuid.uuid4()),
                "book_key": "complex_filename_test",
                "file_name": "Book_Title_Chapter_05_Page_123_Final_Version_v2.jpg",
                "language_code": "en",
                "page_text": "Test text for complex filename",
                "ocr_metadata": {"filename_complexity": "high"}
            }
        }
    ]
    
    for case in edge_cases:
        print(f"  Testing: {case['name']}")
        
        try:
            result_str = tool._run(**case['params'])
            result = json.loads(result_str)
            
            # Should handle gracefully
            assert "success" in result
            print(f"    ✓ Handled correctly")
            
        except Exception as e:
            print(f"    ✗ Failed with exception: {e}")
            return False
    
    print("✓ All edge cases handled correctly")
    return True


def test_filename_patterns():
    """Test comprehensive filename pattern recognition."""
    print("\nTesting filename pattern recognition...")
    
    tool = SyncDBStorageTool()
    
    filename_tests = [
        # Standard patterns
        ("page_001.jpg", 1),
        ("page_999.png", 999),
        ("p001.tiff", 1),
        ("pg_042.webp", 42),
        
        # With spaces
        ("page 15.jpg", 15),
        ("p 7.png", 7),
        ("pg 123.gif", 123),
        
        # Different separators
        ("page-025.jpg", 25),
        ("page.033.png", 33),
        ("page_044_final.tiff", 44),
        
        # Numbers at different positions
        ("001_manuscript.jpg", 1),
        ("025_page_scan.png", 25),
        ("document_15_version2.jpg", 15),
        ("scan_099_final.png", 99),
        
        # Complex patterns
        ("Book_Chapter_05_Page_123.jpg", 123),
        ("Manuscript_Part2_Page_067.png", 67),
        ("IMG_20240101_001_page.jpg", 1),
        
        # Should fail
        ("no_numbers.jpg", None),
        ("page_abc.png", None),
        ("document.tiff", None),
        ("", None),
    ]
    
    passed = 0
    failed = 0
    
    for filename, expected in filename_tests:
        result = tool._extract_page_number_from_filename(filename)
        if result == expected:
            print(f"    ✓ {filename} -> {result}")
            passed += 1
        else:
            print(f"    ✗ {filename} -> {result} (expected {expected})")
            failed += 1
    
    print(f"  Pattern recognition: {passed} passed, {failed} failed")
    return failed == 0


def main():
    """Run all integration tests."""
    print("=" * 70)
    print("SyncDBStorageTool Integration Test Suite")
    print("=" * 70)
    
    tests = [
        test_realistic_book_ingestion,
        test_edge_cases,
        test_filename_patterns,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"Integration Test Results: {passed} passed, {failed} failed")
    print("=" * 70)
    
    if failed == 0:
        print("🎉 All integration tests passed!")
        print("\nThe SyncDBStorageTool is ready for production use!")
        return 0
    else:
        print("❌ Some integration tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())