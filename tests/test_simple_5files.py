#!/usr/bin/env python3
"""SIMPLE test - process 5 files directly"""

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

from sparkjar_shared.tools.google_drive_tool import GoogleDriveTool
from sparkjar_shared.tools.google_drive_download_tool import GoogleDriveDownloadTool  
from sparkjar_shared.tools.image_viewer_tool import ImageViewerTool
from sparkjar_shared.tools.sync_db_storage_tool import SyncDBStorageTool
from crews.book_ingestion_crew.utils import sort_book_files

async def process_5_files():
    """Process 5 files with minimal overhead - KISS approach"""
    
    start_time = time.time()
    
    # Test inputs
    client_user_id = "3a411a30-1653-4caf-acee-de257ff50e36"
    folder_url = "https://drive.google.com/drive/u/0/folders/1HFDpMUHT0wjVWdWB9XIUMYavmq23I4JO"
    
    print("\n" + "="*60)
    print("SIMPLE Book Ingestion Test - 5 Files")
    print("="*60)
    
    # Step 1: Get file list (NO DOWNLOAD)
    print("\n1. Getting file list...")
    drive_tool = GoogleDriveTool()
    result = drive_tool._run(
        folder_path=folder_url,
        client_user_id=client_user_id,
        download=False  # Just get list!
    )
    
    files_data = json.loads(result)
    if files_data["status"] != "success":
        print(f"❌ Failed to get files: {files_data}")
        return
        
    # Filter and sort files
    all_files = files_data["files"]
    image_files = [f for f in all_files if f['name'].lower().endswith(('.png', '.jpg', '.jpeg'))]
    sorted_files = sort_book_files(image_files)[:5]  # Just 5 files
    
    print(f"Found {len(image_files)} images, processing first 5:")
    for f in sorted_files:
        print(f"  - {f['file_name']} (page {f['calculated_page_number']})")
    
    # Process each file
    download_tool = GoogleDriveDownloadTool()
    ocr_tool = ImageViewerTool()
    storage_tool = SyncDBStorageTool()
    
    successful = 0
    failed = 0
    
    for file_info in sorted_files:
        print(f"\n2. Processing {file_info['file_name']}...")
        
        try:
            # Download ONE file
            print("   Downloading...")
            download_result = download_tool._run(
                file_id=file_info['file_id'],
                file_name=file_info['file_name'],
                client_user_id=client_user_id
            )
            download_data = json.loads(download_result)
            
            if not download_data.get("success"):
                print(f"   ❌ Download failed: {download_data}")
                failed += 1
                continue
                
            # OCR the file (3 passes built into the tool)
            print("   Running OCR (3 passes)...")
            ocr_result = ocr_tool._run(download_data["local_path"])
            ocr_data = json.loads(ocr_result)
            
            if "error" in ocr_data:
                print(f"   ❌ OCR failed: {ocr_data}")
                failed += 1
                continue
                
            # Store in database
            print("   Storing in database...")
            storage_result = storage_tool._run(
                client_user_id=client_user_id,
                book_key=folder_url,
                page_number=file_info['calculated_page_number'],
                file_name=file_info['file_name'],
                language_code="es",
                page_text=ocr_data["transcription"],
                ocr_metadata={
                    "file_id": file_info['file_id'],
                    "stats": ocr_data.get("stats", {})
                }
            )
            storage_data = json.loads(storage_result)
            
            if storage_data.get("success"):
                print(f"   ✅ Success! Page ID: {storage_data['page_id']}")
                successful += 1
            else:
                print(f"   ❌ Storage failed: {storage_data}")
                failed += 1
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            failed += 1
    
    # Summary
    elapsed = time.time() - start_time
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Total time: {elapsed:.1f}s")
    print(f"Average per page: {elapsed/5:.1f}s")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"{'='*60}")

if __name__ == "__main__":
    asyncio.run(process_5_files())