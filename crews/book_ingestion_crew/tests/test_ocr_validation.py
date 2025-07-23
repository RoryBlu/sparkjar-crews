#!/usr/bin/env python3
"""
OCR validation test to verify top-line capture accuracy.

This module validates that the OCR process captures the top 4-5 lines
of each manuscript page as required.

Requirements: 2.2 (top-line capture validation)
"""
import json
import logging
from typing import Dict, List, Any, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class OCRValidationTester:
    """Validate OCR output quality and top-line capture."""
    
    def __init__(self):
        self.validation_results = []
        self.known_first_lines = {
            # Add known first lines from test manuscript pages
            # These would be manually verified from the actual manuscript
            1: "La Baron de la Drogo",  # Example - replace with actual
            2: "Capítulo Uno",          # Example - replace with actual
            # Add more as needed
        }
    
    def validate_ocr_output(self, ocr_result: Dict[str, Any], page_number: int) -> Dict[str, Any]:
        """
        Validate a single OCR output.
        
        Args:
            ocr_result: OCR result dictionary with transcription and metadata
            page_number: Page number being validated
            
        Returns:
            Validation result dictionary
        """
        validation = {
            'page_number': page_number,
            'checks': [],
            'passed': True,
            'score': 0.0
        }
        
        transcription = ocr_result.get('transcription', '')
        
        # Check 1: Transcription exists and is not empty
        has_text = bool(transcription and transcription.strip())
        validation['checks'].append({
            'name': 'has_text',
            'passed': has_text,
            'message': 'Transcription contains text' if has_text else 'No text found'
        })
        
        if not has_text:
            validation['passed'] = False
            return validation
        
        # Check 2: Multiple lines captured (top 4-5 lines requirement)
        lines = transcription.strip().split('\n')
        line_count = len(lines)
        has_multiple_lines = line_count >= 4
        
        validation['checks'].append({
            'name': 'multiple_lines',
            'passed': has_multiple_lines,
            'message': f'Captured {line_count} lines' + (' (meets 4+ requirement)' if has_multiple_lines else ' (below 4-line requirement)')
        })
        
        # Check 3: First line content (if known)
        if page_number in self.known_first_lines:
            expected_first = self.known_first_lines[page_number].lower()
            actual_first = lines[0].lower() if lines else ''
            first_line_match = expected_first in actual_first or actual_first in expected_first
            
            validation['checks'].append({
                'name': 'first_line_match',
                'passed': first_line_match,
                'message': f'First line {"matches" if first_line_match else "does not match"} expected content'
            })
        
        # Check 4: OCR quality indicators
        quality_checks = self._check_ocr_quality(transcription, ocr_result)
        validation['checks'].extend(quality_checks)
        
        # Check 5: Processing statistics
        stats = ocr_result.get('processing_stats', {})
        if stats:
            total_words = stats.get('total_words', 0)
            normal_transcription = stats.get('normal_transcription', 0)
            transcription_ratio = normal_transcription / total_words if total_words > 0 else 0
            
            good_ratio = transcription_ratio >= 0.8
            validation['checks'].append({
                'name': 'transcription_quality',
                'passed': good_ratio,
                'message': f'{transcription_ratio:.1%} normal transcription' + (' (good)' if good_ratio else ' (needs improvement)')
            })
        
        # Calculate overall score
        passed_checks = sum(1 for check in validation['checks'] if check['passed'])
        total_checks = len(validation['checks'])
        validation['score'] = passed_checks / total_checks if total_checks > 0 else 0
        validation['passed'] = validation['score'] >= 0.7  # 70% threshold
        
        return validation
    
    def _check_ocr_quality(self, transcription: str, ocr_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check OCR quality indicators."""
        checks = []
        
        # Check for excessive unclear sections
        unclear_sections = ocr_result.get('unclear_sections', [])
        has_few_unclear = len(unclear_sections) <= 3
        checks.append({
            'name': 'unclear_sections',
            'passed': has_few_unclear,
            'message': f'{len(unclear_sections)} unclear sections' + (' (acceptable)' if has_few_unclear else ' (too many)')
        })
        
        # Check for illegible markers
        illegible_count = transcription.count('[ILLEGIBLE]')
        has_few_illegible = illegible_count <= 2
        checks.append({
            'name': 'illegible_markers',
            'passed': has_few_illegible,
            'message': f'{illegible_count} illegible markers' + (' (acceptable)' if has_few_illegible else ' (too many)')
        })
        
        # Check minimum word count (assuming at least 20 words for 4-5 lines)
        word_count = len(transcription.split())
        has_enough_words = word_count >= 20
        checks.append({
            'name': 'word_count',
            'passed': has_enough_words,
            'message': f'{word_count} words' + (' (sufficient)' if has_enough_words else ' (too few)')
        })
        
        return checks
    
    def validate_batch(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate a batch of OCR results.
        
        Args:
            results: List of page results from crew execution
            
        Returns:
            Batch validation summary
        """
        batch_summary = {
            'total_pages': len(results),
            'pages_validated': 0,
            'pages_passed': 0,
            'average_score': 0.0,
            'issues': [],
            'page_validations': []
        }
        
        for result in results:
            if result.get('status') == 'success':
                page_number = result.get('page_number', 0)
                ocr_result = result.get('ocr_result', {})
                
                validation = self.validate_ocr_output(ocr_result, page_number)
                batch_summary['page_validations'].append(validation)
                batch_summary['pages_validated'] += 1
                
                if validation['passed']:
                    batch_summary['pages_passed'] += 1
                else:
                    batch_summary['issues'].append({
                        'page': page_number,
                        'score': validation['score'],
                        'failed_checks': [
                            check['name'] for check in validation['checks'] 
                            if not check['passed']
                        ]
                    })
        
        # Calculate average score
        if batch_summary['page_validations']:
            batch_summary['average_score'] = sum(
                v['score'] for v in batch_summary['page_validations']
            ) / len(batch_summary['page_validations'])
        
        return batch_summary
    
    def generate_report(self, batch_summary: Dict[str, Any]) -> str:
        """Generate a human-readable validation report."""
        report_lines = [
            "OCR VALIDATION REPORT",
            "=" * 50,
            f"Total Pages: {batch_summary['total_pages']}",
            f"Pages Validated: {batch_summary['pages_validated']}",
            f"Pages Passed: {batch_summary['pages_passed']}",
            f"Average Score: {batch_summary['average_score']:.1%}",
            ""
        ]
        
        # Add per-page details
        report_lines.append("PAGE DETAILS:")
        report_lines.append("-" * 50)
        
        for validation in batch_summary['page_validations']:
            status = "✅" if validation['passed'] else "❌"
            report_lines.append(f"\nPage {validation['page_number']}: {status} (Score: {validation['score']:.1%})")
            
            for check in validation['checks']:
                check_status = "✓" if check['passed'] else "✗"
                report_lines.append(f"  {check_status} {check['name']}: {check['message']}")
        
        # Add issues summary
        if batch_summary['issues']:
            report_lines.extend([
                "",
                "ISSUES FOUND:",
                "-" * 50
            ])
            for issue in batch_summary['issues']:
                report_lines.append(
                    f"Page {issue['page']}: Failed checks - {', '.join(issue['failed_checks'])}"
                )
        
        return "\n".join(report_lines)


def validate_test_run_output(output_file: str) -> Tuple[bool, str]:
    """
    Validate the output from a test run.
    
    Args:
        output_file: Path to JSON file with test run output
        
    Returns:
        Tuple of (passed, report)
    """
    validator = OCRValidationTester()
    
    # Load test output
    with open(output_file, 'r') as f:
        test_output = json.load(f)
    
    # Extract detailed results
    detailed_results = test_output.get('detailed_results', [])
    
    # Validate the batch
    batch_summary = validator.validate_batch(detailed_results)
    
    # Generate report
    report = validator.generate_report(batch_summary)
    
    # Determine if passed (at least 80% of pages passed)
    pass_rate = batch_summary['pages_passed'] / batch_summary['pages_validated'] if batch_summary['pages_validated'] > 0 else 0
    passed = pass_rate >= 0.8
    
    return passed, report


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) > 1:
        output_file = sys.argv[1]
        passed, report = validate_test_run_output(output_file)
        print(report)
        sys.exit(0 if passed else 1)
    else:
        print("Usage: python test_ocr_validation.py <output_file.json>")
        sys.exit(1)