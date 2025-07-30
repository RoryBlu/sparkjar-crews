#!/usr/bin/env python3
"""
Production runner for Baron de la Drogue manuscript ingestion.
Senior dev mode: No vibing, just disciplined execution.
"""

import os
import sys
import json
import time
import logging
from datetime import datetime

# Set environment variables
os.environ['SPARKJAR_ENV'] = 'development'

# Import the crew
from crews.book_ingestion_crew.crew import kickoff

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Execute the book ingestion for Baron de la Drogue's manuscript."""
    
    print("=" * 80)
    print("🚀 BARON DE LA DROGUE MANUSCRIPT INGESTION")
    print("=" * 80)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Processing 660+ pages of Cuban history...")
    print("=" * 80)
    
    # Load configuration
    config_path = "baron_de_la_drogue_config.json"
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Remove comment fields
    config.pop('_comment', None)
    config.pop('_note', None)
    
    logger.info(f"Configuration loaded: {config}")
    
    # Start timing
    start_time = time.time()
    
    try:
        # Execute the crew
        print("\n📚 Starting book ingestion crew...")
        print("This will take several hours. Each page takes ~30-45 seconds.")
        print("Individual page failures will not stop the process.")
        print("\nProgress will be shown below:")
        print("-" * 80)
        
        result = kickoff(config)
        
        # Calculate total time
        total_time = time.time() - start_time
        hours = int(total_time // 3600)
        minutes = int((total_time % 3600) // 60)
        seconds = int(total_time % 60)
        
        print("\n" + "=" * 80)
        print("✅ INGESTION COMPLETE!")
        print("=" * 80)
        print(f"Total time: {hours}h {minutes}m {seconds}s")
        print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Print summary
        if isinstance(result, dict):
            print("\n📊 SUMMARY:")
            print(f"Total pages: {result.get('total_pages', 0)}")
            print(f"Successfully processed: {result.get('processed_successfully', 0)}")
            print(f"Failed: {result.get('failed', 0)}")
            
            if 'performance_metrics' in result:
                perf = result['performance_metrics']
                print(f"\nPERFORMANCE:")
                print(f"Average time per page: {perf.get('timing', {}).get('average_page_time', 'N/A')}")
                print(f"LLM compliance: {perf.get('llm_usage', {}).get('compliance', 'N/A')}")
                print(f"Average quality score: {perf.get('quality', {}).get('average_score', 'N/A')}")
        
        print("\n🎉 Baron de la Drogue's story has been digitized!")
        print("The manuscript is now in the BookIngestions table.")
        
        # Save detailed results
        results_file = f"baron_ingestion_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\nDetailed results saved to: {results_file}")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Ingestion interrupted by user")
        print("Note: Processed pages have been saved to the database")
    except Exception as e:
        logger.error(f"Error during ingestion: {e}", exc_info=True)
        print(f"\n❌ Error: {str(e)}")
        print("Check the logs for details")
        sys.exit(1)


if __name__ == "__main__":
    main()