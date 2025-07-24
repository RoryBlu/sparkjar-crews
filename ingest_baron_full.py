#!/usr/bin/env python3
"""
Baron de la Drogue FULL manuscript ingestion.
Direct execution using the proven approach from test_simple_5files.py
"""

import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv
import asyncio
import time

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'sparkjar-shared'))

from tools.google_drive_tool import GoogleDriveTool
from tools.google_drive_download_tool import GoogleDriveDownloadTool  
from tools.image_viewer_tool import ImageViewerTool
from tools.sync_db_storage_tool import SyncDBStorageTool
from crews.book_ingestion_crew.utils import sort_book_files


async def process_baron_manuscript():
    """Process the complete Baron de la Drogue manuscript."""
    
    start_time = time.time()
    
    # Configuration
    client_user_id = "3a411a30-1653-4caf-acee-de257ff50e36"
    folder_url = "https://drive.google.com/drive/u/0/folders/1HFDpMUHT0wjVWdWB9XIUMYavmq23I4JO"
    
    print("=" * 80)
    print("🚀 BARON DE LA DROGUE - FULL MANUSCRIPT INGESTION")
    print("=" * 80)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Client: {client_user_id}")
    print(f"Folder: {folder_url}")
    print("Process: ALL pages (no limit)")
    print("=" * 80)
    
    # Step 1: Get file list
    print("\n📂 Getting file list from Google Drive...")
    drive_tool = GoogleDriveTool()
    result = drive_tool._run(
        folder_path=folder_url,
        client_user_id=client_user_id,
        download=False  # Just get list
    )
    
    files_data = json.loads(result)
    if files_data["status"] != "success":
        print(f"❌ Failed to get files: {files_data}")
        return
        
    # Filter and sort files
    all_files = files_data["files"]
    image_files = [f for f in all_files if f["name"].lower().endswith(('.png', '.jpg', '.jpeg'))]
    sorted_files = sort_book_files(image_files)
    
    print(f"✅ Found {len(sorted_files)} image files")
    print(f"   First page: {sorted_files[0]['file_name'] if sorted_files else 'None'}")
    print(f"   Last page: {sorted_files[-1]['file_name'] if sorted_files else 'None'}")
    
    # Initialize tools
    download_tool = GoogleDriveDownloadTool()
    ocr_tool = ImageViewerTool()
    storage_tool = SyncDBStorageTool()
    
    # Process each page
    print(f"\n🚀 Starting processing of {len(sorted_files)} pages...")
    print("Progress:")
    print("-" * 80)
    
    successful = []
    failed = []
    
    for idx, file_info in enumerate(sorted_files, 1):
        page_start = time.time()
        page_number = file_info["calculated_page_number"]
        file_name = file_info["file_name"]
        file_id = file_info["file_id"]
        
        try:
            # Progress indicator
            progress = (idx / len(sorted_files)) * 100
            print(f"\n[{idx}/{len(sorted_files)}] ({progress:.1f}%) Processing page {page_number}: {file_name}")
            
            # Download
            print("  📥 Downloading...", end='', flush=True)
            download_result = download_tool._run(
                file_id=file_id,
                file_name=file_name,
                client_user_id=client_user_id
            )
            download_data = json.loads(download_result)
            if not download_data.get("success"):
                raise Exception(f"Download failed: {download_data.get('error')}")
            print(" ✓")
            
            # OCR
            print("  👁️ Running 3-pass OCR...", end='', flush=True)
            ocr_result = ocr_tool._run(
                image_path=download_data["local_path"]
            )
            ocr_data = json.loads(ocr_result)
            if ocr_data.get("status") != "success":
                raise Exception(f"OCR failed: {ocr_data.get('error')}")
            print(" ✓")
            
            # Store
            print("  💾 Storing in database...", end='', flush=True)
            storage_result = storage_tool._run(
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
                    "quality_score": ocr_data.get("quality_score", 0.0)
                }
            )
            storage_data = json.loads(storage_result)
            if not storage_data.get("success"):
                raise Exception(f"Storage failed: {storage_data.get('error')}")
            print(" ✓")
            
            # Page complete
            page_time = time.time() - page_start
            print(f"  ⏱️ Page completed in {page_time:.1f}s")
            
            successful.append({
                "page": page_number,
                "file": file_name,
                "time": page_time,
                "quality": ocr_data.get("quality_score", 0.0)
            })
            
            # Cleanup temp file
            try:
                os.remove(download_data["local_path"])
            except:
                pass
                
        except Exception as e:
            print(f"\n  ❌ Error: {str(e)}")
            failed.append({
                "page": page_number,
                "file": file_name,
                "error": str(e)
            })
            continue
    
    # Final summary
    total_time = time.time() - start_time
    hours = int(total_time // 3600)
    minutes = int((total_time % 3600) // 60)
    seconds = int(total_time % 60)
    
    print("\n" + "=" * 80)
    print("✅ MANUSCRIPT INGESTION COMPLETE!")
    print("=" * 80)
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total duration: {hours}h {minutes}m {seconds}s")
    print(f"\n📊 RESULTS:")
    print(f"Total pages: {len(sorted_files)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    print(f"Success rate: {(len(successful)/len(sorted_files)*100):.1f}%")
    
    if successful:
        avg_time = sum(p["time"] for p in successful) / len(successful)
        avg_quality = sum(p["quality"] for p in successful) / len(successful)
        print(f"\nPERFORMANCE:")
        print(f"Average time per page: {avg_time:.1f}s")
        print(f"Average OCR quality: {avg_quality:.2f}")
    
    if failed:
        print(f"\n⚠️ FAILED PAGES ({len(failed)}):")
        for f in failed[:10]:  # Show first 10
            print(f"  - Page {f['page']}: {f['error']}")
        if len(failed) > 10:
            print(f"  ... and {len(failed) - 10} more")
    
    # Save complete results
    results = {
        "start_time": datetime.fromtimestamp(start_time).isoformat(),
        "end_time": datetime.now().isoformat(),
        "duration_seconds": total_time,
        "total_pages": len(sorted_files),
        "successful": len(successful),
        "failed": len(failed),
        "success_rate": (len(successful)/len(sorted_files)*100) if sorted_files else 0,
        "successful_pages": successful,
        "failed_pages": failed
    }
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"baron_manuscript_results_{timestamp}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: {output_file}")
    print("\n🎉 Baron de la Drogue's manuscript has been digitized!")
    print("The complete text is now in the BookIngestions table.")


if __name__ == "__main__":
    print("Starting Baron de la Drogue manuscript ingestion...")
    print("This will process ALL pages - estimated 7-8 hours")
    print("Press Ctrl+C to interrupt (processed pages will be saved)")
    print()
    
    asyncio.run(process_baron_manuscript())