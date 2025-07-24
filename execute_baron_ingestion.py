#!/usr/bin/env python3
"""
Execute Baron de la Drogue manuscript ingestion.
Direct execution - no vibing, pure discipline.
"""

import os
import sys
import json
import time
import logging
import asyncio
from datetime import datetime

# Set environment
os.environ['SPARKJAR_ENV'] = 'development'

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def execute_full_manuscript():
    """Execute the full manuscript ingestion."""
    
    print("=" * 80)
    print("🚀 BARON DE LA DROGUE MANUSCRIPT INGESTION")
    print("=" * 80)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Processing: 660+ handwritten pages")
    print("Language: Spanish")
    print("Method: Sequential processing with 3-pass OCR")
    print("=" * 80)
    
    # Import crew components
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'crews/book_ingestion_crew'))
    from crew import manual_loop_orchestrator
    
    # Configuration
    inputs = {
        "client_user_id": "3a411a30-1653-4caf-acee-de257ff50e36",
        "google_drive_folder_path": "https://drive.google.com/drive/u/0/folders/1HFDpMUHT0wjVWdWB9XIUMYavmq23I4JO",
        "language": "es",
        "job_id": f"baron-manuscript-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        # NO process_pages_limit - process ALL pages
    }
    
    print("\n📚 Starting crew execution...")
    print("Expected duration: ~7-8 hours for 660+ pages")
    print("Progress will be shown in real-time below:")
    print("-" * 80)
    
    start_time = time.time()
    
    try:
        # Execute the crew
        result = manual_loop_orchestrator(inputs)
        
        # Calculate duration
        total_time = time.time() - start_time
        hours = int(total_time // 3600)
        minutes = int((total_time % 3600) // 60)
        seconds = int(total_time % 60)
        
        print("\n" + "=" * 80)
        print("✅ MANUSCRIPT INGESTION COMPLETE!")
        print("=" * 80)
        print(f"Total processing time: {hours}h {minutes}m {seconds}s")
        print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Display results
        if isinstance(result, dict):
            print(f"\n📊 RESULTS:")
            print(f"Total pages in folder: {result.get('total_pages', 0)}")
            print(f"Successfully processed: {result.get('processed_successfully', 0)}")
            print(f"Failed pages: {result.get('failed', 0)}")
            print(f"Processing time: {result.get('processing_time', 'N/A')}")
            
            # Performance metrics
            if 'performance_metrics' in result:
                perf = result['performance_metrics']
                print(f"\n⚡ PERFORMANCE:")
                print(f"Average per page: {perf['timing']['average_page_time']}")
                print(f"LLM compliance: {perf['llm_usage']['compliance']}")
                print(f"Total LLM calls: {perf['llm_usage']['total_calls']}")
                
            # Quality metrics  
            if 'quality_metrics' in result:
                quality = result['quality_metrics']
                print(f"\n📈 QUALITY:")
                print(f"Average OCR score: {quality['average_quality_score']:.2f}")
                print(f"High quality pages: {quality['high_quality_pages']}")
                print(f"Pages needing review: {quality['pages_requiring_review']}")
                
            # Resource usage
            if 'resource_usage' in result:
                resources = result['resource_usage']
                print(f"\n💾 RESOURCES:")
                print(f"Temp files cleaned: {resources['temp_files']['cleaned']}")
                print(f"Peak disk usage: {resources['temp_files']['peak_space_mb']}MB")
        
        print("\n🎉 Baron de la Drogue's manuscript has been successfully digitized!")
        print("All pages are now stored in the BookIngestions table.")
        
        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_file = f"baron_manuscript_complete_{timestamp}.json"
        with open(results_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\n📄 Complete results saved to: {results_file}")
        
        return result
        
    except KeyboardInterrupt:
        elapsed = time.time() - start_time
        print(f"\n\n⚠️ Ingestion interrupted after {elapsed/60:.1f} minutes")
        print("Already processed pages remain in the database")
        return None
    except Exception as e:
        logger.error(f"Critical error: {e}", exc_info=True)
        print(f"\n❌ Error: {str(e)}")
        return None


def main():
    """Main entry point."""
    result = asyncio.run(execute_full_manuscript())
    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()