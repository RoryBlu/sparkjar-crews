#!/usr/bin/env python3
"""Resume Baron de la Drogue manuscript ingestion from checkpoint"""

import os
import sys
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# Add sparkjar-shared to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'sparkjar-shared'))

# Import the book ingestion crew
from crews.book_ingestion_crew.crew import kickoff, get_files_from_drive, sort_book_files

# Configuration files
CONFIG_FILE = "baron_de_la_drogue_config.json"
PROGRESS_FILE = "baron_progress.json"

def load_config():
    """Load Baron de la Drogue configuration"""
    if not os.path.exists(CONFIG_FILE):
        raise FileNotFoundError(f"Configuration file not found: {CONFIG_FILE}")
    
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def load_progress():
    """Load progress tracking data"""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {
        "processed_pages": [],
        "failed_pages": [],
        "last_update": None
    }

def save_progress(progress):
    """Save progress tracking data"""
    progress["last_update"] = datetime.utcnow().isoformat()
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)
    logger.info(f"Progress saved: {len(progress['processed_pages'])} pages completed")

def calculate_remaining_pages(all_files, processed_pages):
    """Calculate which pages still need processing"""
    from crews.book_ingestion_crew.utils import parse_baron_filename
    
    # Extract page numbers from filenames
    remaining_files = []
    
    for file_info in all_files:
        filename = file_info.get('file_name') or file_info.get('name')
        if not filename:
            continue
            
        page_num = None
        
        # Try to parse as baron format first
        try:
            baron_info = parse_baron_filename(filename)
            page_num = baron_info['page_number']
            file_info['calculated_page_number'] = page_num
        except:
            # Try simple numeric format (e.g., "409.png" -> 409)
            try:
                page_num = int(filename.split('.')[0])
                file_info['calculated_page_number'] = page_num
            except:
                # If we can't parse page number, skip it
                logger.warning(f"Cannot parse page number from filename: {filename}")
                continue
        
        if page_num and page_num not in processed_pages:
            remaining_files.append(file_info)
    
    return remaining_files

def process_single_page(config, page_number, file_name, file_id):
    """Process a single page using the crew"""
    # Prepare inputs for single page processing
    crew_inputs = {
        "job_key": "book_ingestion_crew",
        "google_drive_folder_path": config["google_drive_folder_path"],
        "language": config["language"],
        "client_user_id": config["client_user_id"],
        "actor_type": "user",
        "actor_id": "baron-manuscript-processor",
        "book_title": "Baron de la Drogue",
        "book_author": "Castor Gonzalez",
        "book_description": "The autobiography of Castor Gonzalez",
        # Override the file listing to process just this one file
        "_single_file_mode": True,
        "_target_file": {
            "file_name": file_name,
            "file_id": file_id,
            "calculated_page_number": page_number
        }
    }
    
    # Since the crew doesn't support single file mode directly,
    # we'll use a workaround by creating a custom crew instance
    from crews.book_ingestion_crew.crew import build_production_crew
    from tools.google_drive_download_tool import GoogleDriveDownloadTool
    from tools.image_viewer_tool import ImageViewerTool
    from tools.sync_db_storage_tool import SyncDBStorageTool
    
    try:
        # Create crew
        crew = build_production_crew(config["client_user_id"])
        
        # Prepare page input
        page_input = {
            "client_user_id": config["client_user_id"],
            "book_key": config["google_drive_folder_path"],
            "page_number": page_number,
            "file_name": file_name,
            "file_id": file_id,
            "google_drive_folder_path": config["google_drive_folder_path"],
            "language_code": config["language"]
        }
        
        # Process single page
        result = crew.kickoff(inputs=page_input)
        
        # Check if successful
        if hasattr(result, 'raw'):
            result_str = result.raw
        else:
            result_str = str(result)
        
        success = "success" in result_str.lower() and "error" not in result_str.lower()
        
        return success, result_str
        
    except Exception as e:
        logger.error(f"Error processing page {page_number}: {e}")
        return False, str(e)

def main():
    """Resume Baron de la Drogue manuscript processing"""
    print("\n" + "="*60)
    print("Baron de la Drogue Manuscript Ingestion - RESUME")
    print("="*60 + "\n")
    
    try:
        # Load configuration
        config = load_config()
        logger.info(f"Configuration loaded: {CONFIG_FILE}")
        
        # Load progress
        progress = load_progress()
        processed_count = len(progress['processed_pages'])
        logger.info(f"Previous progress: {processed_count} pages already processed")
        
        if processed_count > 0:
            logger.info(f"Last processed pages: {sorted(progress['processed_pages'])[-5:]}")
        
        # Get all files from Google Drive
        logger.info("\nFetching file list from Google Drive...")
        inputs = {
            "google_drive_folder_path": config["google_drive_folder_path"],
            "client_user_id": config["client_user_id"]
        }
        
        all_files = get_files_from_drive(inputs)
        sorted_files = sort_book_files(all_files)
        total_pages = len(sorted_files)
        
        logger.info(f"Total pages in manuscript: {total_pages}")
        
        # Calculate remaining pages
        remaining_files = calculate_remaining_pages(sorted_files, progress['processed_pages'])
        remaining_count = len(remaining_files)
        
        if remaining_count == 0:
            print("\n✅ Manuscript is already fully processed!")
            print(f"Total pages: {total_pages}")
            return
        
        # Sort remaining files by page number (they should already have calculated_page_number from calculate_remaining_pages)
        remaining_files.sort(key=lambda f: f.get('calculated_page_number', 9999))
        
        print(f"\n📊 Progress Status:")
        print(f"   - Total pages: {total_pages}")
        print(f"   - Completed: {processed_count} ({processed_count/total_pages*100:.1f}%)")
        print(f"   - Remaining: {remaining_count}")
        print(f"   - Next pages: {[f['file_name'] for f in remaining_files[:5]]}")
        print(f"   - Estimated time: {remaining_count * 50 / 60:.1f} minutes")
        
        # Ask for confirmation
        response = input("\n🚀 Ready to process remaining pages? (y/n): ")
        if response.lower() != 'y':
            print("Cancelled.")
            return
        
        print("\n" + "="*60)
        print("Starting processing...")
        print("="*60 + "\n")
        
        # Process pages one by one
        start_time = time.time()
        initial_processed = processed_count
        consecutive_failures = 0
        max_consecutive_failures = 5
        
        for i, file_info in enumerate(remaining_files):
            page_num = file_info.get('calculated_page_number')
            if not page_num:
                logger.warning(f"No calculated page number for file: {file_info.get('file_name')}")
                continue
            
            # Skip if already processed (double check)
            if page_num in progress['processed_pages']:
                continue
            
            logger.info(f"\nProcessing page {page_num} ({i+1}/{remaining_count}): {file_info['file_name']}")
            
            try:
                # Process single page
                success, result = process_single_page(
                    config, 
                    page_num, 
                    file_info['file_name'], 
                    file_info['file_id']
                )
                
                if success:
                    progress['processed_pages'].append(page_num)
                    consecutive_failures = 0
                    logger.info(f"✅ Page {page_num} processed successfully")
                else:
                    progress['failed_pages'].append(page_num)
                    consecutive_failures += 1
                    logger.error(f"❌ Page {page_num} failed: {result[:100]}")
                
                # Save progress every 10 pages or after failures
                if (len(progress['processed_pages']) % 10 == 0) or not success:
                    save_progress(progress)
                
                # Calculate and show progress
                processed_so_far = len(progress['processed_pages']) - initial_processed
                if processed_so_far > 0:
                    elapsed = time.time() - start_time
                    avg_time = elapsed / processed_so_far
                    pages_left = remaining_count - (i + 1)
                    eta_seconds = pages_left * avg_time
                    
                    if (i + 1) % 5 == 0:  # Show progress every 5 pages
                        print(f"\n📈 Progress Update:")
                        print(f"   - Current: Page {page_num}")
                        print(f"   - Completed this session: {processed_so_far}")
                        print(f"   - Total completed: {len(progress['processed_pages'])}/{total_pages} ({len(progress['processed_pages'])/total_pages*100:.1f}%)")
                        print(f"   - Average time per page: {avg_time:.1f}s")
                        print(f"   - ETA: {eta_seconds/60:.1f} minutes")
                
                # Check for too many consecutive failures
                if consecutive_failures >= max_consecutive_failures:
                    logger.error(f"\n⚠️  Too many consecutive failures ({consecutive_failures}). Stopping.")
                    save_progress(progress)
                    break
                    
            except KeyboardInterrupt:
                print("\n\n⚠️  Processing interrupted by user")
                save_progress(progress)
                print(f"Progress saved. Completed {len(progress['processed_pages'])} pages.")
                print("Run this script again to resume.")
                return
            except Exception as e:
                logger.error(f"Error processing page {page_num}: {e}")
                progress['failed_pages'].append(page_num)
                consecutive_failures += 1
                save_progress(progress)
                
                if consecutive_failures >= max_consecutive_failures:
                    logger.error(f"\n⚠️  Too many consecutive failures. Stopping.")
                    break
        
        # Final save
        save_progress(progress)
        
        # Final summary
        elapsed_total = time.time() - start_time
        pages_processed_session = len(progress['processed_pages']) - initial_processed
        
        print("\n" + "="*60)
        if len(progress['processed_pages']) >= total_pages:
            print("✅ MANUSCRIPT COMPLETE!")
        else:
            print("📊 SESSION COMPLETE")
        print("="*60)
        
        print(f"\nSession Statistics:")
        print(f"  - Pages processed this session: {pages_processed_session}")
        print(f"  - Session time: {elapsed_total/60:.1f} minutes")
        if pages_processed_session > 0:
            print(f"  - Average time per page: {elapsed_total/pages_processed_session:.1f}s")
        
        print(f"\nOverall Statistics:")
        print(f"  - Total pages processed: {len(progress['processed_pages'])}/{total_pages}")
        print(f"  - Failed pages: {len(progress['failed_pages'])}")
        print(f"  - Success rate: {(len(progress['processed_pages']) / total_pages * 100):.1f}%")
        print(f"  - Remaining pages: {total_pages - len(progress['processed_pages'])}")
        
        if progress['failed_pages']:
            print(f"\n⚠️  Failed pages: {sorted(progress['failed_pages'])[:10]}")
            if len(progress['failed_pages']) > 10:
                print(f"     ... and {len(progress['failed_pages']) - 10} more")
            
        if len(progress['processed_pages']) >= total_pages:
            print("\n🎉 Baron de la Drogue manuscript digitization complete!")
        else:
            print(f"\n💡 Run this script again to continue processing remaining {total_pages - len(progress['processed_pages'])} pages")
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())