"""Production Book Ingestion Crew - processes pages individually with proper logging"""
from pathlib import Path
import yaml
from crewai import Agent, Crew, Process, Task
import logging
from typing import Dict, Any, List
import json
import time
import os

# Direct OpenAI configuration for gpt-4.1 models
import openai
openai.api_key = os.environ.get('OPENAI_API_KEY')

# Import needed tools
from tools.google_drive_tool import GoogleDriveTool
from tools.google_drive_download_tool import GoogleDriveDownloadTool
from tools.image_viewer_tool import ImageViewerTool
from tools.sync_db_storage_tool import SyncDBStorageTool

# Import utility functions
from crews.book_ingestion_crew.utils import parse_baron_filename, sort_book_files

logger = logging.getLogger(__name__)

CONFIG_DIR = Path(__file__).parent / "config"

def _load_yaml(file_name: str):
    """Load YAML configuration."""
    path = CONFIG_DIR / file_name
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def build_production_crew(client_user_id: str) -> Crew:
    """Build production crew for page processing."""
    
    # Create file download agent
    download_agent = Agent(
        role="File Downloader",
        goal="Download individual files from Google Drive",
        backstory="Efficient at retrieving files one at a time",
        tools=[GoogleDriveDownloadTool()],
        verbose=False,
        model="gpt-4.1-nano"
    )
    
    # Create OCR agent - THIS IS JUST THE COORDINATOR, NOT THE OCR TOOL
    ocr_agent = Agent(
        role="OCR Coordinator",
        goal="Coordinate OCR tool usage - the tool does the actual OCR with gpt-4o",
        backstory="Coordinates the image viewer tool which uses gpt-4o for OCR",
        tools=[ImageViewerTool()],
        verbose=False,
        model="gpt-4.1-mini"  # Agent just coordinates, tool uses gpt-4o
    )
    
    # Create storage agent
    storage_agent = Agent(
        role="Data Storage Specialist", 
        goal="Store transcribed pages reliably in database",
        backstory="Database expert ensuring proper data storage and integrity",
        tools=[SyncDBStorageTool()],
        verbose=False,
        model="gpt-4.1-nano"  # Use mini for storage tasks
    )
    
    # Create tasks for page processing - KEEP SIMPLE TO REDUCE LLM CALLS
    download_task = Task(
        description="""Call GoogleDriveDownloadTool with file_id={file_id}, file_name={file_name}, client_user_id={client_user_id}""",
        expected_output="local_path",
        agent=download_agent
    )
    
    ocr_task = Task(
        description="""Call ImageViewerTool with the local_path from previous task. Tool handles OCR.""",
        expected_output="transcription",
        agent=ocr_agent,
        context=[download_task]
    )
    
    storage_task = Task(
        description="""Call SyncDBStorageTool with client_user_id={client_user_id}, book_key={book_key}, page_number={page_number}, file_name={file_name}, language_code={language_code}, page_text=<OCR_RESULT>, ocr_metadata={{"file_id":"{file_id}"}}""",
        expected_output="success",
        agent=storage_agent,
        context=[ocr_task]
    )
    
    # Create crew
    crew = Crew(
        agents=[download_agent, ocr_agent, storage_agent],
        tasks=[download_task, ocr_task, storage_task],
        process=Process.sequential,
        verbose=False,
        memory=False  # Disable CrewAI memory
    )
    
    return crew

def get_files_from_drive(inputs: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get LIST of files from Google Drive - NO DOWNLOADS."""
    drive_tool = GoogleDriveTool()
    
    # Just get the file list, no downloads!
    result = drive_tool._run(
        folder_path=inputs["google_drive_folder_path"],
        client_user_id=inputs["client_user_id"],
        download=False  # NO DOWNLOADS - just get the list!
    )
    
    if isinstance(result, str):
        try:
            result = json.loads(result)
        except:
            logger.error(f"Failed to parse drive result: {result}")
            return []
    
    if isinstance(result, dict) and result.get("status") == "success":
        files = result.get("files", [])
        # Support all image types
        image_extensions = ('.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp', '.tiff')
        image_files = [f for f in files if f.get('name', '').lower().endswith(image_extensions)]
        logger.info(f"Total files in folder: {len(files)}, Image files: {len(image_files)}")
        return image_files
    else:
        logger.error(f"Failed to list files: {result}")
        return []

def kickoff(inputs: Dict[str, Any], simple_logger=None) -> Dict[str, Any]:
    """
    Execute production book ingestion crew.
    
    This processes pages individually using kickoff_for_each.
    All agent output is captured in crew_job_event table.
    """
    start_time = time.time()
    
    if simple_logger:
        simple_logger.log({
            "event_type": "crew_start",
            "message": "Starting production book ingestion crew",
            "timestamp": time.time()
        })
    
    client_user_id = inputs.get("client_user_id")
    if not client_user_id:
        raise ValueError("client_user_id is required")
    
    # Get process limit if specified
    process_limit = inputs.get("process_pages_limit")
    
    # Step 1: Get files from Google Drive
    logger.info("Fetching files from Google Drive...")
    if simple_logger:
        simple_logger.log({
            "event_type": "task_start",
            "task": "fetch_files",
            "message": "Fetching files from Google Drive"
        })
    
    files = get_files_from_drive(inputs)
    logger.info(f"Found {len(files)} image files")
    
    if not files:
        return {
            "status": "error",
            "error": "No image files found in folder",
            "total_pages": 0
        }
    
    # Step 2: Sort files by page number
    sorted_files = sort_book_files(files)
    
    # Apply limit if specified
    if process_limit:
        sorted_files = sorted_files[:process_limit]
        logger.info(f"Limited to processing {process_limit} pages")
    
    # Debug: Show what files we're processing
    logger.info(f"Files to process: {[f['file_name'] for f in sorted_files]}")
    
    # Step 3: Build crew
    crew = build_production_crew(client_user_id)
    
    # Step 4: Prepare inputs for each page
    page_inputs = []
    book_key = inputs.get("google_drive_folder_path")
    language_code = inputs.get("language", "es")
    
    for file_info in sorted_files:
        # Since we didn't download files yet, we'll pass the file_id
        # The crew will download one file at a time
        page_input = {
            "client_user_id": client_user_id,
            "book_key": book_key,
            "page_number": file_info["calculated_page_number"],
            "file_name": file_info["file_name"],
            "file_id": file_info["file_id"],
            "google_drive_folder_path": inputs["google_drive_folder_path"],  # Need this for download
            "language_code": language_code
        }
        page_inputs.append(page_input)
    
    logger.info(f"Processing {len(page_inputs)} pages with kickoff_for_each")
    
    if simple_logger:
        simple_logger.log({
            "event_type": "task_start", 
            "task": "process_pages",
            "message": f"Processing {len(page_inputs)} pages individually",
            "page_count": len(page_inputs)
        })
    
    # Step 5: Process pages ONE AT A TIME
    results = []
    for page_input in page_inputs:
        logger.info(f"Processing page {page_input['page_number']}: {page_input['file_name']}")
        result = crew.kickoff(inputs=page_input)
        results.append(result)
    
    # Step 6: Compile results
    successful = []
    failed = []
    
    for i, result in enumerate(results):
        page_info = page_inputs[i]
        
        if hasattr(result, 'raw'):
            result_str = result.raw
        else:
            result_str = str(result)
        
        # Check if storage was successful
        if "success" in result_str.lower() and "error" not in result_str.lower():
            successful.append({
                "page_number": page_info["page_number"],
                "file_name": page_info["file_name"]
            })
        else:
            failed.append({
                "page_number": page_info["page_number"],
                "file_name": page_info["file_name"],
                "error": result_str[:200]  # First 200 chars of error
            })
    
    elapsed_time = time.time() - start_time
    
    # Create summary
    summary = {
        "status": "completed",
        "total_pages": len(page_inputs),
        "processed_successfully": len(successful), 
        "failed": len(failed),
        "processing_time": f"{elapsed_time:.1f}s",
        "average_time_per_page": f"{elapsed_time/len(page_inputs):.1f}s" if page_inputs else "0s",
        "successful_pages": successful,
        "failed_pages": failed
    }
    
    logger.info(f"Completed processing. Success: {len(successful)}, Failed: {len(failed)}")
    
    if simple_logger:
        simple_logger.log({
            "event_type": "crew_complete",
            "message": f"Completed processing {len(page_inputs)} pages",
            "successful": len(successful),
            "failed": len(failed),
            "elapsed_time": elapsed_time
        })
    
    return summary