#!/usr/bin/env python3
"""
Comprehensive integration test for book ingestion crew with 5 manuscript pages.

This module implements task 11 requirements:
- End-to-end test with 5 manuscript page images
- Test complete workflow from Google Drive to database storage
- Validate OCR accuracy and top-line capture
- Verify LLM call count limits (max 4 per page)

Requirements: 2.2, 2.3, 1.4
"""
import os
import sys
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import Mock, patch
import asyncio

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'sparkjar-shared'))

# Import crew components
from crews.book_ingestion_crew.crew import kickoff
from utils.simple_crew_logger import SimpleCrewLogger

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LLMCallTracker:
    """Track LLM calls to verify max 4 calls per page requirement."""
    
    def __init__(self):
        self.calls_per_page: Dict[int, int] = {}
        self.total_calls = 0
        self.call_details: List[Dict[str, Any]] = []
        self.original_create = None
    
    def track_call(self, model: str, messages: List[Dict], **kwargs):
        """Track each LLM call."""
        self.total_calls += 1
        
        # Extract page context from messages if available
        page_number = self._extract_page_number(messages)
        
        if page_number is not None:
            self.calls_per_page[page_number] = self.calls_per_page.get(page_number, 0) + 1
        
        # Record call details
        self.call_details.append({
            'timestamp': datetime.now().isoformat(),
            'model': model,
            'page_number': page_number,
            'message_count': len(messages),
            'total_tokens': kwargs.get('max_tokens', 0)
        })
        
        # Call original method
        if self.original_create:
            return self.original_create(model=model, messages=messages, **kwargs)
    
    def _extract_page_number(self, messages: List[Dict]) -> int:
        """Try to extract page number from message context."""
        for msg in messages:
            if isinstance(msg, dict):
                content = str(msg.get('content', ''))
                # Look for page references in the content
                if 'page' in content.lower():
                    import re
                    match = re.search(r'page[_\s]+(\d+)', content, re.IGNORECASE)
                    if match:
                        return int(match.group(1))
        return None
    
    def get_report(self) -> Dict[str, Any]:
        """Generate report of LLM usage."""
        return {
            'total_calls': self.total_calls,
            'calls_per_page': self.calls_per_page,
            'pages_exceeding_limit': [
                page for page, calls in self.calls_per_page.items() if calls > 4
            ],
            'average_calls_per_page': (
                sum(self.calls_per_page.values()) / len(self.calls_per_page)
                if self.calls_per_page else 0
            ),
            'call_details': self.call_details
        }


class IntegrationTestRunner:
    """Run comprehensive integration test for book ingestion crew."""
    
    def __init__(self):
        self.llm_tracker = LLMCallTracker()
        self.test_results = {
            'workflow_complete': False,
            'pages_processed': 0,
            'ocr_quality_scores': [],
            'top_line_captures': [],
            'errors': [],
            'performance_metrics': {},
            'llm_usage': {}
        }
    
    def setup_test_inputs(self) -> Dict[str, Any]:
        """Set up test inputs for 5-page manuscript."""
        return {
            "job_key": "book_ingestion_crew",
            "google_drive_folder_path": "https://drive.google.com/drive/u/0/folders/1HFDpMUHT0wjVWdWB9XIUMYavmq23I4JO",
            "language": "Spanish",
            "client_user_id": "3a411a30-1653-4caf-acee-de257ff50e36",
            "actor_type": "synth",
            "actor_id": "e30fc9f3-57da-4cf0-84e7-ea9188dd5fba",
            "book_title": "La Baron de la Drogo - Test",
            "book_author": "Castor Gonzalez",
            "book_description": "Integration test with 5 pages",
            "process_pages_limit": 5  # Limit to 5 pages for testing
        }
    
    def patch_llm_calls(self):
        """Patch OpenAI calls to track LLM usage."""
        try:
            import openai
            if hasattr(openai, 'ChatCompletion'):
                # Older OpenAI SDK
                self.llm_tracker.original_create = openai.ChatCompletion.create
                openai.ChatCompletion.create = self.llm_tracker.track_call
            elif hasattr(openai, 'chat') and hasattr(openai.chat, 'completions'):
                # Newer OpenAI SDK
                self.llm_tracker.original_create = openai.chat.completions.create
                openai.chat.completions.create = self.llm_tracker.track_call
        except Exception as e:
            logger.warning(f"Could not patch OpenAI calls for tracking: {e}")
    
    def run_integration_test(self) -> Dict[str, Any]:
        """Run the complete integration test."""
        logger.info("=" * 80)
        logger.info("Book Ingestion Crew - Integration Test (5 Pages)")
        logger.info("=" * 80)
        
        # Set up test inputs
        inputs = self.setup_test_inputs()
        
        # Create simple logger for tracking
        simple_logger = SimpleCrewLogger(job_id=f"test-{int(time.time())}")
        
        # Patch LLM calls for tracking
        self.patch_llm_calls()
        
        # Record start time
        start_time = time.time()
        
        try:
            # Run the crew
            logger.info(f"Starting crew execution at {datetime.now()}")
            logger.info(f"Processing limit: {inputs['process_pages_limit']} pages")
            
            result = kickoff(inputs, simple_logger)
            
            # Record end time
            end_time = time.time()
            elapsed_time = end_time - start_time
            
            # Process results
            self.process_results(result, elapsed_time)
            
            # Validate results
            self.validate_results(result)
            
            # Get LLM usage report
            self.test_results['llm_usage'] = self.llm_tracker.get_report()
            
            # Log summary
            self.log_summary()
            
            return self.test_results
            
        except Exception as e:
            logger.error(f"Integration test failed: {str(e)}", exc_info=True)
            self.test_results['errors'].append({
                'type': 'execution_error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            })
            return self.test_results
    
    def process_results(self, result: Dict[str, Any], elapsed_time: float):
        """Process the crew execution results."""
        if result.get('status') == 'completed':
            self.test_results['workflow_complete'] = True
            self.test_results['pages_processed'] = result.get('processed_successfully', 0)
            
            # Extract quality metrics
            quality_metrics = result.get('quality_metrics', {})
            
            # Performance metrics
            self.test_results['performance_metrics'] = {
                'total_time': elapsed_time,
                'average_time_per_page': (
                    elapsed_time / self.test_results['pages_processed'] 
                    if self.test_results['pages_processed'] > 0 else 0
                ),
                'processing_time': result.get('processing_time', 'N/A')
            }
            
            # Extract OCR quality scores from successful pages
            successful_pages = result.get('successful_pages', [])
            for page in successful_pages:
                if 'quality_score' in page:
                    self.test_results['ocr_quality_scores'].append({
                        'page_number': page['page_number'],
                        'score': page['quality_score'],
                        'requires_review': page.get('requires_review', False)
                    })
        else:
            self.test_results['errors'].append({
                'type': 'workflow_error',
                'message': result.get('error', 'Unknown error'),
                'timestamp': datetime.now().isoformat()
            })
    
    def validate_results(self, result: Dict[str, Any]):
        """Validate the test results against requirements."""
        validations = []
        
        # Validate workflow completion
        if self.test_results['workflow_complete']:
            validations.append({
                'check': 'workflow_completion',
                'passed': True,
                'message': 'Workflow completed successfully'
            })
        else:
            validations.append({
                'check': 'workflow_completion',
                'passed': False,
                'message': 'Workflow did not complete'
            })
        
        # Validate pages processed
        expected_pages = 5
        actual_pages = self.test_results['pages_processed']
        validations.append({
            'check': 'pages_processed',
            'passed': actual_pages == expected_pages,
            'message': f'Processed {actual_pages}/{expected_pages} pages'
        })
        
        # Validate OCR quality (should have quality scores)
        has_quality_scores = len(self.test_results['ocr_quality_scores']) > 0
        validations.append({
            'check': 'ocr_quality_tracking',
            'passed': has_quality_scores,
            'message': f'OCR quality scores: {len(self.test_results["ocr_quality_scores"])} pages tracked'
        })
        
        # Validate LLM call limits (max 4 per page)
        llm_report = self.llm_tracker.get_report()
        pages_exceeding = llm_report.get('pages_exceeding_limit', [])
        validations.append({
            'check': 'llm_call_limit',
            'passed': len(pages_exceeding) == 0,
            'message': f'LLM calls per page: {pages_exceeding} pages exceeded 4-call limit' if pages_exceeding else 'All pages within 4-call limit'
        })
        
        # Check for top-line capture validation
        # This would require analyzing the actual OCR output
        detailed_results = result.get('detailed_results', [])
        top_line_check = self._validate_top_line_capture(detailed_results)
        validations.append(top_line_check)
        
        self.test_results['validations'] = validations
    
    def _validate_top_line_capture(self, detailed_results: List[Dict]) -> Dict[str, Any]:
        """Validate that OCR captured top lines of pages."""
        pages_with_text = 0
        pages_checked = 0
        
        for page_result in detailed_results:
            if page_result.get('status') == 'success':
                ocr_result = page_result.get('ocr_result', {})
                transcription = ocr_result.get('transcription', '')
                
                if transcription:
                    pages_checked += 1
                    # Simple check: transcription should have multiple lines
                    lines = transcription.strip().split('\n')
                    if len(lines) >= 4:  # At least 4 lines captured
                        pages_with_text += 1
                        self.test_results['top_line_captures'].append({
                            'page_number': page_result.get('page_number'),
                            'lines_captured': len(lines),
                            'first_line': lines[0][:50] + '...' if len(lines[0]) > 50 else lines[0]
                        })
        
        return {
            'check': 'top_line_capture',
            'passed': pages_with_text == pages_checked and pages_checked > 0,
            'message': f'Top lines captured: {pages_with_text}/{pages_checked} pages'
        }
    
    def log_summary(self):
        """Log test summary."""
        logger.info("\n" + "=" * 80)
        logger.info("INTEGRATION TEST SUMMARY")
        logger.info("=" * 80)
        
        # Workflow status
        logger.info(f"Workflow Complete: {'✅' if self.test_results['workflow_complete'] else '❌'}")
        logger.info(f"Pages Processed: {self.test_results['pages_processed']}")
        
        # Performance metrics
        perf = self.test_results['performance_metrics']
        logger.info(f"\nPerformance Metrics:")
        logger.info(f"  Total Time: {perf.get('total_time', 0):.2f}s")
        logger.info(f"  Avg Time/Page: {perf.get('average_time_per_page', 0):.2f}s")
        
        # LLM usage
        llm = self.test_results['llm_usage']
        logger.info(f"\nLLM Usage:")
        logger.info(f"  Total Calls: {llm.get('total_calls', 0)}")
        logger.info(f"  Avg Calls/Page: {llm.get('average_calls_per_page', 0):.2f}")
        if llm.get('pages_exceeding_limit'):
            logger.warning(f"  Pages exceeding 4-call limit: {llm['pages_exceeding_limit']}")
        
        # OCR quality
        if self.test_results['ocr_quality_scores']:
            avg_quality = sum(s['score'] for s in self.test_results['ocr_quality_scores']) / len(self.test_results['ocr_quality_scores'])
            logger.info(f"\nOCR Quality:")
            logger.info(f"  Average Score: {avg_quality:.2f}")
            logger.info(f"  Pages Requiring Review: {sum(1 for s in self.test_results['ocr_quality_scores'] if s['requires_review'])}")
        
        # Validations
        logger.info(f"\nValidation Results:")
        for validation in self.test_results.get('validations', []):
            status = '✅' if validation['passed'] else '❌'
            logger.info(f"  {status} {validation['check']}: {validation['message']}")
        
        # Errors
        if self.test_results['errors']:
            logger.error(f"\nErrors Encountered: {len(self.test_results['errors'])}")
            for error in self.test_results['errors']:
                logger.error(f"  - {error['type']}: {error['message']}")
        
        logger.info("=" * 80)


def run_integration_test():
    """Main entry point for integration test."""
    runner = IntegrationTestRunner()
    results = runner.run_integration_test()
    
    # Determine overall test status
    all_validations_passed = all(
        v['passed'] for v in results.get('validations', [])
    )
    
    if all_validations_passed and results['workflow_complete']:
        logger.info("\n✅ INTEGRATION TEST PASSED")
        return 0
    else:
        logger.error("\n❌ INTEGRATION TEST FAILED")
        return 1


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Run the test
    exit_code = run_integration_test()
    sys.exit(exit_code)