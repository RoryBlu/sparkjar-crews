#!/usr/bin/env python3
"""
Run full Baron de la Drogue manuscript ingestion.
Using the same approach as test_simple_5files.py but without page limit.
"""

import os
import asyncio
import json
import time
from datetime import datetime

# Set environment
os.environ['SPARKJAR_ENV'] = 'development'


async def process_full_manuscript():
    """Process the complete Baron de la Drogue manuscript."""
    
    print("=" * 80)
    print("🚀 BARON DE LA DROGUE FULL MANUSCRIPT INGESTION")
    print("=" * 80)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Target: ALL pages in Google Drive folder")
    print("Estimated: 660+ handwritten pages")
    print("Duration: ~7-8 hours")
    print("=" * 80)
    
    # Import crew-api components
    from services.crew_api.src.services.job_service import execute_crew_job
    from services.crew_api.src.services.crew_service import get_crew_handler
    
    # Configuration
    crew_key = "book_ingestion_crew"
    job_id = f"baron-full-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    request_data = {
        "client_user_id": "3a411a30-1653-4caf-acee-de257ff50e36",
        "google_drive_folder_path": "https://drive.google.com/drive/u/0/folders/1HFDpMUHT0wjVWdWB9XIUMYavmq23I4JO",
        "language": "es"
        # NO process_pages_limit - process ALL pages
    }
    
    print("\n📚 Initializing crew handler...")
    handler = get_crew_handler(crew_key, job_id)
    
    print("✅ Handler initialized")
    print("\n🚀 Starting manuscript processing...")
    print("Progress will be shown below:")
    print("-" * 80)
    
    start_time = time.time()
    
    try:
        # Execute the crew
        result = await handler.execute(request_data)
        
        # Calculate duration
        total_time = time.time() - start_time
        hours = int(total_time // 3600)
        minutes = int((total_time % 3600) // 60)
        seconds = int(total_time % 60)
        
        print("\n" + "=" * 80)
        print("✅ MANUSCRIPT PROCESSING COMPLETE!")
        print("=" * 80)
        print(f"Total time: {hours}h {minutes}m {seconds}s")
        print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Show results
        if isinstance(result, dict):
            print(f"\n📊 RESULTS:")
            print(f"Status: {result.get('status', 'unknown')}")
            print(f"Total pages: {result.get('total_pages', 0)}")
            print(f"Processed: {result.get('processed_successfully', 0)}")
            print(f"Failed: {result.get('failed', 0)}")
            
            # Save complete results
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"baron_manuscript_final_{timestamp}.json"
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"\n📄 Full results saved to: {output_file}")
        
        print("\n🎉 Baron de la Drogue's manuscript has been digitized!")
        print("The complete text is now available in the BookIngestions table.")
        
        return result
        
    except KeyboardInterrupt:
        elapsed = time.time() - start_time
        print(f"\n\n⚠️ Processing interrupted after {elapsed/60:.1f} minutes")
        print("Completed pages are saved in the database")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        if hasattr(handler, 'cleanup'):
            await handler.cleanup()


if __name__ == "__main__":
    # Add the project root to Python path
    import sys
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, project_root)
    
    # Run the processing
    asyncio.run(process_full_manuscript())