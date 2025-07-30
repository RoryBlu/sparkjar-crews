#!/usr/bin/env python3
"""
Baron de la Drogue Manuscript Ingestion
Senior dev mode: No vibing, disciplined execution only.
"""

import os
import sys
import json
import time
import logging
from datetime import datetime

# Set environment
os.environ['SPARKJAR_ENV'] = 'development'

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Execute the full manuscript ingestion."""
    
    print("=" * 80)
    print("🚀 BARON DE LA DROGUE MANUSCRIPT INGESTION")
    print("=" * 80)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Target: 660+ pages of handwritten Cuban history")
    print("Mode: Sequential processing with 3-pass OCR")
    print("=" * 80)
    
    # Import after environment is set
    from test_simple_5files import test_book_ingestion_small_batch
    
    # Configuration for full manuscript
    inputs = {
        "client_user_id": "3a411a30-1653-4caf-acee-de257ff50e36",
        "google_drive_folder_path": "https://drive.google.com/drive/u/0/folders/1HFDpMUHT0wjVWdWB9XIUMYavmq23I4JO",
        "language": "es",
        # NO LIMIT - process all pages
    }
    
    print("\n📚 Starting ingestion...")
    print("Expected duration: 7-8 hours for 660+ pages")
    print("Each page: ~30-45 seconds (download + 3-pass OCR + storage)")
    print("\nProgress updates will appear below:")
    print("-" * 80)
    
    start_time = time.time()
    
    try:
        # Execute using the test framework
        result = test_book_ingestion_small_batch(
            client_user_id=inputs["client_user_id"],
            folder_path=inputs["google_drive_folder_path"],
            language=inputs["language"],
            process_limit=None  # Process ALL pages
        )
        
        # Calculate duration
        total_time = time.time() - start_time
        hours = int(total_time // 3600)
        minutes = int((total_time % 3600) // 60)
        seconds = int(total_time % 60)
        
        print("\n" + "=" * 80)
        print("✅ MANUSCRIPT INGESTION COMPLETE!")
        print("=" * 80)
        print(f"Total time: {hours}h {minutes}m {seconds}s")
        print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Show summary
        if result and 'result' in result:
            summary = result['result']
            print(f"\n📊 FINAL SUMMARY:")
            print(f"Total pages processed: {summary.get('total_pages', 0)}")
            print(f"Successfully ingested: {summary.get('processed_successfully', 0)}")
            print(f"Failed pages: {summary.get('failed', 0)}")
            
            # Performance metrics
            if 'performance_metrics' in summary:
                perf = summary['performance_metrics']['timing']
                print(f"\nPERFORMANCE METRICS:")
                print(f"Average time per page: {perf.get('average_page_time', 'N/A')}")
                print(f"Total execution time: {perf.get('total_execution_time', 'N/A')}")
            
            # Quality metrics
            if 'quality_metrics' in summary:
                quality = summary['quality_metrics']
                print(f"\nQUALITY METRICS:")
                print(f"Average OCR quality: {quality.get('average_quality_score', 0):.2f}")
                print(f"Pages requiring review: {quality.get('pages_requiring_review', 0)}")
        
        print("\n🎉 Baron de la Drogue's manuscript has been digitized!")
        print("The complete text is now in the BookIngestions table.")
        
        # Save detailed results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_file = f"baron_manuscript_results_{timestamp}.json"
        with open(results_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\nDetailed results saved to: {results_file}")
        
    except KeyboardInterrupt:
        elapsed = time.time() - start_time
        print(f"\n\n⚠️ Ingestion interrupted after {elapsed/60:.1f} minutes")
        print("Note: Already processed pages are saved in the database")
    except Exception as e:
        logger.error(f"Error during ingestion: {e}", exc_info=True)
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()