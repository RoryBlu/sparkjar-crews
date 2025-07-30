#!/usr/bin/env python3
"""
Resume Baron de la Drogue manuscript ingestion from page 409.
Handles the remaining 238 pages with improved error handling and progress tracking.
"""

import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv
import asyncio
import time
from typing import Dict, List, Optional

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'sparkjar-shared'))

from tools.google_drive_tool import GoogleDriveTool
from tools.google_drive_download_tool import GoogleDriveDownloadTool  
from tools.image_viewer_tool import ImageViewerTool
from tools.sync_db_storage_tool import SyncDBStorageTool
from crews.book_ingestion_crew.utils import sort_book_files


class ProgressTracker:
    """Track and save progress for resumability."""
    
    def __init__(self, checkpoint_file: str = "baron_progress.json"):
        self.checkpoint_file = checkpoint_file
        self.processed_pages = set()
        self.failed_pages = []
        self.load_checkpoint()
    
    def load_checkpoint(self):
        """Load existing checkpoint if available."""
        if os.path.exists(self.checkpoint_file):
            try:
                with open(self.checkpoint_file, 'r') as f:
                    data = json.load(f)
                    self.processed_pages = set(data.get('processed_pages', []))
                    self.failed_pages = data.get('failed_pages', [])
                print(f"📂 Loaded checkpoint: {len(self.processed_pages)} pages already processed")
            except:
                pass
    
    def save_checkpoint(self):
        """Save current progress."""
        data = {
            'processed_pages': list(self.processed_pages),
            'failed_pages': self.failed_pages,
            'last_update': datetime.now().isoformat()
        }
        with open(self.checkpoint_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def mark_processed(self, page_number: int):
        """Mark a page as processed."""
        self.processed_pages.add(page_number)
        if len(self.processed_pages) % 10 == 0:  # Save every 10 pages
            self.save_checkpoint()
    
    def mark_failed(self, page_info: Dict):
        """Mark a page as failed."""
        self.failed_pages.append(page_info)
        self.save_checkpoint()
    
    def is_processed(self, page_number: int) -> bool:
        """Check if page was already processed."""
        return page_number in self.processed_pages


async def process_page_with_timeout(page_info: Dict, tools: Dict, client_user_id: str, 
                                  folder_url: str, max_retries: int = 3) -> Optional[Dict]:
    """Process a single page with timeout and retry logic."""
    page_number = page_info["calculated_page_number"]
    file_name = page_info["file_name"]
    file_id = page_info["file_id"]
    
    for attempt in range(max_retries):
        try:
            # Download with 2-minute timeout
            print(f"  📥 Downloading (attempt {attempt + 1})...", end='', flush=True)
            download_start = time.time()
            download_result = tools['download']._run(
                file_id=file_id,
                file_name=file_name,
                client_user_id=client_user_id
            )
            download_time = time.time() - download_start
            
            # Timeout check
            if download_time > 120:
                print(f" ⚠️ Slow download: {download_time:.1f}s")
            else:
                print(" ✓")
            
            download_data = json.loads(download_result)
            if not download_data.get("success"):
                raise Exception(f"Download failed: {download_data.get('error')}")
            
            # OCR with 5-minute timeout warning
            print(f"  👁️ Running 3-pass OCR...", end='', flush=True)
            ocr_start = time.time()
            ocr_result = tools['ocr']._run(image_path=download_data["local_path"])
            ocr_time = time.time() - ocr_start
            
            if ocr_time > 300:  # 5 minutes
                print(f" ⚠️ Slow OCR: {ocr_time:.1f}s")
            else:
                print(" ✓")
            
            ocr_data = json.loads(ocr_result)
            if ocr_data.get("status") != "success":
                raise Exception(f"OCR failed: {ocr_data.get('error')}")
            
            # Store in database
            print(f"  💾 Storing in database...", end='', flush=True)
            storage_result = tools['storage']._run(
                client_user_id=client_user_id,
                book_key=folder_url,
                page_number=page_number,
                file_name=file_name,
                language_code="es",
                page_text=ocr_data["transcription"],
                ocr_metadata={
                    "file_id": file_id,
                    "processing_stats": ocr_data.get("processing_stats", {}),
                    "ocr_passes": 3,
                    "quality_score": ocr_data.get("quality_score", 0.0),
                    "processing_time": {
                        "download_seconds": download_time,
                        "ocr_seconds": ocr_time
                    }
                }
            )
            storage_data = json.loads(storage_result)
            if not storage_data.get("success"):
                raise Exception(f"Storage failed: {storage_data.get('error')}")
            print(" ✓")
            
            # Cleanup temp file
            try:
                os.remove(download_data["local_path"])
            except:
                pass
            
            # Return success info
            return {
                "page": page_number,
                "file": file_name,
                "time": download_time + ocr_time,
                "quality": ocr_data.get("quality_score", 0.0),
                "attempt": attempt + 1
            }
            
        except Exception as e:
            print(f"\n  ❌ Attempt {attempt + 1} failed: {str(e)}")
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 5  # Progressive backoff
                print(f"  ⏳ Waiting {wait_time}s before retry...")
                await asyncio.sleep(wait_time)
            else:
                return None


async def resume_manuscript_processing():
    """Resume processing from page 479 through the end."""
    
    start_time = time.time()
    
    # Configuration
    client_user_id = "3a411a30-1653-4caf-acee-de257ff50e36"
    folder_url = "https://drive.google.com/drive/u/0/folders/1HFDpMUHT0wjVWdWB9XIUMYavmq23I4JO"
    START_PAGE = 481  # Resume from this page number (480/baron020 4.png confirmed in DB)
    
    print("=" * 80)
    print("🔄 RESUMING BARON DE LA DROGUE MANUSCRIPT INGESTION")
    print("=" * 80)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Starting from: Page {START_PAGE} (baron017 8.png)")
    print(f"Client: {client_user_id}")
    print("=" * 80)
    
    # Initialize progress tracker
    tracker = ProgressTracker()
    
    # Get file list
    print("\n📂 Getting file list from Google Drive...")
    drive_tool = GoogleDriveTool()
    result = drive_tool._run(
        folder_path=folder_url,
        client_user_id=client_user_id,
        download=False
    )
    
    files_data = json.loads(result)
    if files_data["status"] != "success":
        print(f"❌ Failed to get files: {files_data}")
        return
    
    # Filter and sort files
    all_files = files_data["files"]
    image_files = [f for f in all_files if f["name"].lower().endswith(('.png', '.jpg', '.jpeg'))]
    sorted_files = sort_book_files(image_files)
    
    # Filter to only process pages >= START_PAGE
    remaining_files = [f for f in sorted_files if f["calculated_page_number"] >= START_PAGE]
    
    # Also check against tracker
    files_to_process = []
    for f in remaining_files:
        if not tracker.is_processed(f["calculated_page_number"]):
            files_to_process.append(f)
    
    print(f"✅ Total files in folder: {len(sorted_files)}")
    print(f"📊 Already completed: {START_PAGE - 1} pages")
    print(f"🎯 Remaining to process: {len(files_to_process)} pages")
    
    if files_to_process:
        print(f"   First page: {files_to_process[0]['file_name']} (page {files_to_process[0]['calculated_page_number']})")
        print(f"   Last page: {files_to_process[-1]['file_name']} (page {files_to_process[-1]['calculated_page_number']})")
    
    # Initialize tools
    tools = {
        'download': GoogleDriveDownloadTool(),
        'ocr': ImageViewerTool(),
        'storage': SyncDBStorageTool()
    }
    
    # Process remaining pages
    print(f"\n🚀 Starting processing of {len(files_to_process)} remaining pages...")
    print("Progress:")
    print("-" * 80)
    
    successful = []
    failed = []
    
    for idx, file_info in enumerate(files_to_process, 1):
        page_start = time.time()
        page_number = file_info["calculated_page_number"]
        file_name = file_info["file_name"]
        
        # Progress indicator
        overall_progress = ((START_PAGE - 1 + idx) / len(sorted_files)) * 100
        batch_progress = (idx / len(files_to_process)) * 100
        print(f"\n[{idx}/{len(files_to_process)}] Overall: {overall_progress:.1f}% | Batch: {batch_progress:.1f}%")
        print(f"Processing page {page_number}: {file_name}")
        
        # Process with timeout and retry
        result = await process_page_with_timeout(file_info, tools, client_user_id, folder_url)
        
        if result:
            # Success
            page_time = time.time() - page_start
            print(f"  ⏱️ Page completed in {page_time:.1f}s (quality: {result['quality']:.2f})")
            successful.append(result)
            tracker.mark_processed(page_number)
        else:
            # Failed after retries
            print(f"  ❌ Failed to process page {page_number} after all retries")
            failed_info = {
                "page": page_number,
                "file": file_name,
                "error": "Failed after max retries"
            }
            failed.append(failed_info)
            tracker.mark_failed(failed_info)
        
        # Show estimated time remaining
        if successful:
            avg_time = sum(p["time"] for p in successful) / len(successful)
            remaining_pages = len(files_to_process) - idx
            eta_seconds = remaining_pages * avg_time
            eta_hours = int(eta_seconds // 3600)
            eta_minutes = int((eta_seconds % 3600) // 60)
            print(f"  ⏰ ETA: {eta_hours}h {eta_minutes}m ({remaining_pages} pages remaining)")
    
    # Final summary
    total_time = time.time() - start_time
    hours = int(total_time // 3600)
    minutes = int((total_time % 3600) // 60)
    seconds = int(total_time % 60)
    
    print("\n" + "=" * 80)
    print("✅ MANUSCRIPT PROCESSING COMPLETE!")
    print("=" * 80)
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Session duration: {hours}h {minutes}m {seconds}s")
    
    print(f"\n📊 SESSION RESULTS:")
    print(f"Pages processed: {len(successful)}")
    print(f"Pages failed: {len(failed)}")
    print(f"Success rate: {(len(successful)/(len(successful)+len(failed))*100):.1f}%")
    
    print(f"\n📚 OVERALL MANUSCRIPT STATUS:")
    total_completed = START_PAGE - 1 + len(successful)
    print(f"Total pages in manuscript: {len(sorted_files)}")
    print(f"Total pages completed: {total_completed}")
    print(f"Overall completion: {(total_completed/len(sorted_files)*100):.1f}%")
    
    if successful:
        avg_time = sum(p["time"] for p in successful) / len(successful)
        avg_quality = sum(p["quality"] for p in successful) / len(successful)
        print(f"\nPERFORMANCE:")
        print(f"Average time per page: {avg_time:.1f}s")
        print(f"Average OCR quality: {avg_quality:.2f}")
    
    if failed:
        print(f"\n⚠️ FAILED PAGES ({len(failed)}):")
        for f in failed:
            print(f"  - Page {f['page']} ({f['file']}): {f.get('error', 'Unknown error')}")
    
    # Save final progress
    tracker.save_checkpoint()
    
    # Save complete session results
    session_results = {
        "session_start": datetime.fromtimestamp(start_time).isoformat(),
        "session_end": datetime.now().isoformat(),
        "session_duration_seconds": total_time,
        "start_page": START_PAGE,
        "pages_processed": len(successful),
        "pages_failed": len(failed),
        "total_completed": total_completed,
        "manuscript_total": len(sorted_files),
        "completion_percentage": (total_completed/len(sorted_files)*100),
        "successful_pages": successful,
        "failed_pages": failed
    }
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_file = f"baron_resume_results_{timestamp}.json"
    with open(results_file, 'w') as f:
        json.dump(session_results, f, indent=2)
    
    print(f"\n📄 Session results saved to: {results_file}")
    
    if total_completed >= len(sorted_files):
        print("\n🎉 CONGRATULATIONS! Baron de la Drogue's complete manuscript has been digitized!")
        print("The entire 646-page handwritten story is now preserved in digital form.")
    else:
        remaining = len(sorted_files) - total_completed
        print(f"\n📝 {remaining} pages still remaining to complete the manuscript.")
    


if __name__ == "__main__":
    print("Starting Baron de la Drogue manuscript completion...")
    print("Resuming from page 409 (baron017 8.png)")
    print("Press Ctrl+C to interrupt (progress is saved automatically)")
    print()
    
    asyncio.run(resume_manuscript_processing())