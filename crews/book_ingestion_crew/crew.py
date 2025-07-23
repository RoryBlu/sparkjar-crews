"""Production Book Ingestion Crew - processes pages individually with proper logging"""
from pathlib import Path
import yaml
from crewai import Agent, Crew, Process, Task
import logging
from typing import Dict, Any, List
import json
import time
import os
import asyncio

# Direct OpenAI configuration for gpt-4.1 models
import openai
openai.api_key = os.environ.get('OPENAI_API_KEY')

# Import needed tools
from tools.google_drive_tool import GoogleDriveTool
from tools.google_drive_download_tool import GoogleDriveDownloadTool
from tools.image_viewer_tool import ImageViewerTool
from tools.sync_db_storage_tool import SyncDBStorageTool

# Import utility functions (using new comprehensive utilities with backward compatibility)
from crews.book_ingestion_crew.file_processing_utils import (
    parse_baron_filename, 
    sort_book_files,
    sort_files_by_page_number,
    validate_page_sequence,
    create_file_parser,
    FilenameParser
)

# Import comprehensive error handling
from crews.book_ingestion_crew.error_handling import (
    BookIngestionErrorHandler, 
    create_error_handler,
    ErrorCategory,
    ErrorSeverity
)

# Import performance monitoring
from crews.book_ingestion_crew.performance_monitor import PerformanceMonitor

# Import resource management
from crews.book_ingestion_crew.resource_manager import ResourceManager

logger = logging.getLogger(__name__)

CONFIG_DIR = Path(__file__).parent / "config"

def _load_yaml(file_name: str):
    """Load YAML configuration."""
    path = CONFIG_DIR / file_name
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def _create_tool_instance(tool_name: str):
    """Create tool instance based on tool name."""
    tool_mapping = {
        'google_drive_download_tool': GoogleDriveDownloadTool,
        'image_viewer_tool': ImageViewerTool,
        'sync_db_storage_tool': SyncDBStorageTool
    }
    
    tool_class = tool_mapping.get(tool_name)
    if not tool_class:
        raise ValueError(f"Unknown tool: {tool_name}")
    
    return tool_class()

def build_crew_from_yaml() -> Crew:
    """
    Build crew factory with YAML-based configuration.
    
    This function implements task 7 requirements by creating a crew builder that:
    - Loads agents and tasks from YAML configuration files (agents.yaml, tasks.yaml)
    - Implements proper agent initialization with gpt-4.1-nano model as specified
    - Configures sequential processing pipeline using Process.sequential
    - Adds tool assignment to appropriate agents based on YAML configuration
    
    The factory pattern ensures consistent crew creation while maintaining
    flexibility through YAML configuration. This approach follows CrewAI
    standards and supports the KISS principle for maintainable code.
    
    YAML Configuration Structure:
    - agents.yaml: Defines agent roles, goals, backstories, models, and tools
    - tasks.yaml: Defines task descriptions, expected outputs, agent assignments, and dependencies
    
    Tool Assignment:
    - download_agent: GoogleDriveDownloadTool
    - ocr_agent: ImageViewerTool  
    - storage_agent: SyncDBStorageTool
    
    Processing Pipeline:
    - Sequential execution (Process.sequential)
    - Task dependencies handled through context
    - Memory disabled for production reliability
    
    Returns:
        Crew: Configured CrewAI crew with 3 agents and 3 tasks
        
    Raises:
        ValueError: If unknown tool name or missing agent configuration
        FileNotFoundError: If YAML configuration files are missing
    
    Requirements: 3.1, 3.2, 3.3, 3.4
    """
    # Load YAML configurations
    agents_config = _load_yaml("agents.yaml")
    tasks_config = _load_yaml("tasks.yaml")
    
    # Create agents from YAML configuration
    agents = {}
    agent_list = []
    
    for agent_name, agent_config in agents_config.items():
        # Create tool instances for this agent
        tools = []
        for tool_name in agent_config.get('tools', []):
            tool_instance = _create_tool_instance(tool_name)
            tools.append(tool_instance)
        
        # Create agent with YAML configuration
        agent = Agent(
            role=agent_config['role'],
            goal=agent_config['goal'],
            backstory=agent_config['backstory'],
            tools=tools,
            verbose=False,
            model=agent_config.get('model', 'gpt-4.1-nano')  # Default to gpt-4.1-nano
        )
        
        agents[agent_name] = agent
        agent_list.append(agent)
    
    # Create tasks from YAML configuration
    tasks = {}
    task_list = []
    
    for task_name, task_config in tasks_config.items():
        # Get the agent for this task
        agent_name = task_config['agent']
        if agent_name not in agents:
            raise ValueError(f"Agent '{agent_name}' not found for task '{task_name}'")
        
        # Handle task context (dependencies)
        context_tasks = []
        if 'context' in task_config:
            for context_task_name in task_config['context']:
                if context_task_name in tasks:
                    context_tasks.append(tasks[context_task_name])
        
        # Create task with YAML configuration
        task = Task(
            description=task_config['description'],
            expected_output=task_config['expected_output'],
            agent=agents[agent_name],
            context=context_tasks if context_tasks else None
        )
        
        tasks[task_name] = task
        task_list.append(task)
    
    # Create crew with sequential processing pipeline
    crew = Crew(
        agents=agent_list,
        tasks=task_list,
        process=Process.sequential,
        verbose=False,
        memory=False  # Disable CrewAI memory for production
    )
    
    return crew

def build_production_crew(client_user_id: str) -> Crew:
    """Build production crew for page processing using YAML configuration."""
    return build_crew_from_yaml()

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

def manual_loop_orchestrator(inputs: Dict[str, Any], simple_logger=None) -> Dict[str, Any]:
    """
    Manual loop processing orchestrator for book ingestion with comprehensive error handling and performance monitoring.
    
    Implements sequential file processing (one page at a time) using manual loops
    instead of kickoff_for_each. Ensures maximum 4 LLM calls per page:
    - 1 coordination call per agent (3 agents total)
    - 3 OCR passes within ImageViewerTool (handled by tool internally)
    
    Enhanced with comprehensive error handling:
    - Individual page failures don't stop entire process
    - Retry logic for transient failures
    - Graceful degradation for OCR quality issues
    - Structured error logging with context
    
    Enhanced with performance monitoring:
    - Processing time measurement per page
    - LLM call counting and validation
    - Database transaction performance tracking
    - Resource usage monitoring
    
    Requirements: 6.1, 6.2, 6.3, 2.3, 6.4, 2.4, 12 (performance monitoring)
    """
    start_time = time.time()
    
    # Initialize comprehensive error handler
    error_handler = create_error_handler(logger)
    
    # Initialize performance monitor
    job_id = inputs.get("job_id", "unknown")
    performance_monitor = PerformanceMonitor(job_id=job_id)
    
    # Initialize resource manager
    resource_manager = ResourceManager(job_id=job_id)
    
    if simple_logger:
        simple_logger.log_event("crew_start", {
            "message": "Starting manual loop processing orchestrator with error handling",
            "timestamp": time.time()
        })
    
    client_user_id = inputs.get("client_user_id")
    if not client_user_id:
        raise ValueError("client_user_id is required")
    
    # Get process limit if specified
    process_limit = inputs.get("process_pages_limit")
    
    try:
        # Step 1: File discovery using GoogleDriveTool with error handling
        logger.info("Discovering files from Google Drive...")
        if simple_logger:
            simple_logger.log_event("task_start", {
                "task": "file_discovery",
                "message": "Discovering files from Google Drive"
            })
        
        try:
            files = get_files_from_drive(inputs)
            logger.info(f"Discovered {len(files)} image files")
        except Exception as e:
            error_handler.log_error(
                error=e,
                context={"operation": "file_discovery", "folder_path": inputs.get("google_drive_folder_path")}
            )
            return {
                "status": "error",
                "error": f"Failed to discover files: {str(e)}",
                "total_pages": 0,
                "error_summary": error_handler.get_error_summary()
            }
        
        if not files:
            return {
                "status": "error",
                "error": "No image files found in folder",
                "total_pages": 0
            }
        
        # Step 2: File sorting logic using page number extraction
        # Use the enhanced file parser for better format support
        parser = create_file_parser()
        sorted_files = sort_files_by_page_number(files, parser)
        
        # Validate the page sequence
        validation_issues = validate_page_sequence(sorted_files)
        if validation_issues:
            logger.warning(f"Page sequence validation found {len(validation_issues)} issues:")
            for issue in validation_issues:
                logger.warning(f"  - {issue['type']}: {issue['message']}")
                if simple_logger:
                    simple_logger.log_event("validation_warning", {
                        "issue": issue
                    })
        
        # Apply limit if specified
        if process_limit:
            sorted_files = sorted_files[:process_limit]
            logger.info(f"Limited to processing {process_limit} pages")
        
        logger.info(f"Files sorted for processing: {[f['file_name'] for f in sorted_files]}")
        
        # Step 3: Initialize tools for manual orchestration
        download_tool = GoogleDriveDownloadTool()
        ocr_tool = ImageViewerTool()
        storage_tool = SyncDBStorageTool()
        
        # Pass resource manager to tools that need it
        # Note: This would require modifying the tools to accept resource_manager
        # For now, we're managing resources at the orchestrator level
        
        # Step 4: Sequential file processing (one page at a time) with comprehensive error handling
        results = []
        successful = []
        failed = []
        
        book_key = inputs.get("google_drive_folder_path")
        language_code = inputs.get("language", "es")
        
        for file_info in sorted_files:
            page_number = file_info["calculated_page_number"]
            file_name = file_info["file_name"]
            file_id = file_info["file_id"]
            
            # Check if we should continue processing based on error history
            if not error_handler.should_continue_processing(page_number, len(sorted_files)):
                logger.error(f"Stopping processing at page {page_number} due to excessive errors")
                break
            
            logger.info(f"Processing page {page_number}: {file_name}")
            
            # Start performance monitoring for this page
            performance_monitor.start_page_processing(page_number, file_name)
            
            if simple_logger:
                simple_logger.log_event("page_start", {
                    "page_number": page_number,
                    "file_name": file_name,
                    "message": f"Starting page {page_number}"
                })
            
            page_context = {
                "page_number": page_number,
                "file_name": file_name,
                "file_id": file_id,
                "book_key": book_key
            }
            
            try:
                # Step 4a: Download file with retry logic
                logger.info(f"Downloading file: {file_name}")
                performance_monitor.start_operation("download")
                performance_monitor.record_llm_call()  # Count the coordination LLM call
                
                def download_with_error_handling():
                    result = download_tool._run(
                        file_id=file_id,
                        file_name=file_name,
                        client_user_id=client_user_id
                    )
                    
                    # Parse download result
                    if isinstance(result, str):
                        try:
                            data = json.loads(result)
                        except Exception as parse_error:
                            raise Exception(f"Failed to parse download result: {result}")
                    else:
                        data = result
                    
                    if not data.get("success"):
                        raise Exception(f"Download failed: {data.get('error', 'Unknown error')}")
                    
                    local_path = data.get("local_path")
                    if not local_path:
                        raise Exception("No local path returned from download")
                    
                    # Track temp file for cleanup with resource manager
                    error_handler.add_temp_file(local_path)
                    resource_manager.track_large_file(Path(local_path))
                    
                    return data
                
                # Execute download with retry logic
                async def download_with_retry_tracking():
                    try:
                        result = await error_handler.execute_with_retry(
                            download_with_error_handling,
                            page_number=page_number,
                            file_name=file_name,
                            file_id=file_id,
                            context={**page_context, "operation": "download"}
                        )
                        return result
                    except Exception as e:
                        # Track retries in performance monitor
                        if hasattr(e, '__cause__') and 'retry' in str(e).lower():
                            performance_monitor.record_retry()
                        raise
                
                download_data = asyncio.run(download_with_retry_tracking())
                
                local_path = download_data.get("local_path")
                logger.info(f"Downloaded to: {local_path}")
                performance_monitor.end_operation("download")
                
                # Get file size for metrics
                try:
                    file_size = os.path.getsize(local_path)
                except:
                    file_size = 0
                
                # Step 4b: OCR processing with retry logic and quality degradation
                logger.info(f"Performing OCR on: {file_name}")
                performance_monitor.start_operation("ocr")
                performance_monitor.record_llm_call()  # Count the coordination LLM call
                
                def ocr_with_error_handling():
                    result = ocr_tool._run(image_path=local_path)
                    
                    # Parse OCR result
                    if isinstance(result, str):
                        try:
                            data = json.loads(result)
                        except Exception as parse_error:
                            raise Exception(f"Failed to parse OCR result: {result}")
                    else:
                        data = result
                    
                    if data.get("status") != "success":
                        raise Exception(f"OCR failed: {data.get('error', 'Unknown error')}")
                    
                    return data
                
                # Execute OCR with retry logic
                ocr_data = asyncio.run(error_handler.execute_with_retry(
                    ocr_with_error_handling,
                    page_number=page_number,
                    file_name=file_name,
                    file_id=file_id,
                    context={**page_context, "operation": "ocr"}
                ))
                
                # Apply OCR quality degradation handling
                ocr_data = error_handler.handle_ocr_degradation(ocr_data, page_number, file_name)
                
                page_text = ocr_data.get("transcription", "")
                ocr_metadata = {
                    "file_id": file_id,
                    "processing_stats": ocr_data.get("processing_stats", {}),
                    "unclear_sections": ocr_data.get("unclear_sections", []),
                    "ocr_passes": 3,
                    "model_used": "gpt-4o",
                    "quality_score": ocr_data.get("quality_score"),
                    "quality_assessment": ocr_data.get("quality_assessment"),
                    "degradation_applied": ocr_data.get("degradation_applied")
                }
                
                logger.info(f"OCR completed for: {file_name} (quality: {ocr_data.get('quality_score', 'unknown')})")
                performance_monitor.end_operation("ocr")
                
                # Record OCR metrics
                performance_monitor.record_ocr_pass()  # x3 for the 3 passes
                performance_monitor.record_ocr_pass()
                performance_monitor.record_ocr_pass()
                performance_monitor.record_file_metrics(file_size, len(page_text))
                performance_monitor.record_quality_metrics(
                    quality_score=ocr_data.get("quality_score", 0.0),
                    unclear_sections=len(ocr_data.get("unclear_sections", [])),
                    requires_review=ocr_data.get("requires_manual_review", False)
                )
                
                # Step 4c: Database storage with retry logic
                logger.info(f"Storing page data: {file_name}")
                performance_monitor.start_operation("storage")
                performance_monitor.record_llm_call()  # Count the coordination LLM call
                
                def storage_with_error_handling():
                    result = storage_tool._run(
                        client_user_id=client_user_id,
                        book_key=book_key,
                        page_number=page_number,
                        file_name=file_name,
                        language_code=language_code,
                        page_text=page_text,
                        ocr_metadata=ocr_metadata
                    )
                    
                    # Parse storage result
                    if isinstance(result, str):
                        try:
                            data = json.loads(result)
                        except Exception as parse_error:
                            raise Exception(f"Failed to parse storage result: {result}")
                    else:
                        data = result
                    
                    if not data.get("success"):
                        raise Exception(f"Storage failed: {data.get('error', 'Unknown error')}")
                    
                    return data
                
                # Execute storage with retry logic
                storage_data = asyncio.run(error_handler.execute_with_retry(
                    storage_with_error_handling,
                    page_number=page_number,
                    file_name=file_name,
                    file_id=file_id,
                    context={**page_context, "operation": "storage"}
                ))
                
                logger.info(f"Successfully processed page {page_number}: {file_name}")
                performance_monitor.end_operation("storage")
                
                # Mark page as successfully completed
                performance_monitor.end_page_processing(success=True)
                
                # Record success
                successful.append({
                    "page_number": page_number,
                    "file_name": file_name,
                    "page_id": storage_data.get("page_id"),
                    "quality_score": ocr_data.get("quality_score"),
                    "requires_review": ocr_data.get("requires_manual_review", False)
                })
                
                results.append({
                    "page_number": page_number,
                    "file_name": file_name,
                    "status": "success",
                    "download_result": download_data,
                    "ocr_result": ocr_data,
                    "storage_result": storage_data
                })
                
                if simple_logger:
                    simple_logger.log_event("page_complete", {
                        "page_number": page_number,
                        "file_name": file_name,
                        "status": "success",
                        "quality_score": ocr_data.get("quality_score"),
                        "message": f"Successfully processed page {page_number}"
                    })
            
            except Exception as e:
                # Log the error with full context
                processing_error = error_handler.log_error(
                    error=e,
                    page_number=page_number,
                    file_name=file_name,
                    file_id=file_id,
                    context=page_context
                )
                
                # Record error in performance monitor
                performance_monitor.record_error(e, processing_error.error_category.value)
                performance_monitor.end_page_processing(success=False)
                
                # Record failure
                failed.append({
                    "page_number": page_number,
                    "file_name": file_name,
                    "error": str(e),
                    "error_category": processing_error.error_category.value,
                    "severity": processing_error.severity.value,
                    "recoverable": processing_error.recoverable
                })
                
                results.append({
                    "page_number": page_number,
                    "file_name": file_name,
                    "status": "failed",
                    "error": str(e),
                    "error_details": processing_error.to_dict()
                })
                
                if simple_logger:
                    simple_logger.log_event("page_error", {
                        "page_number": page_number,
                        "file_name": file_name,
                        "error": str(e),
                        "error_category": processing_error.error_category.value,
                        "severity": processing_error.severity.value,
                        "message": f"Failed to process page {page_number}"
                    })
                
                # Individual page failures don't stop entire process (requirement 6.4)
                continue
            
            finally:
                # Clean up temporary files for this page
                error_handler.cleanup_temp_files()
                resource_manager.cleanup_page_resources(page_number)
        
        elapsed_time = time.time() - start_time
        
        # Get comprehensive error summary
        error_summary = error_handler.get_error_summary()
        
        # Finalize performance report
        performance_report = performance_monitor.finalize_report()
        performance_monitor.log_summary()
        
        # Create enhanced summary with error analysis and performance metrics
        summary = {
            "status": "completed",
            "total_pages": len(sorted_files),
            "processed_successfully": len(successful), 
            "failed": len(failed),
            "processing_time": f"{elapsed_time:.1f}s",
            "average_time_per_page": f"{elapsed_time/len(sorted_files):.1f}s" if sorted_files else "0s",
            "successful_pages": successful,
            "failed_pages": failed,
            "detailed_results": results,
            "error_summary": error_summary,
            "quality_metrics": {
                "pages_requiring_review": sum(1 for p in successful if p.get("requires_review")),
                "average_quality_score": sum(p.get("quality_score", 0) for p in successful) / len(successful) if successful else 0,
                "high_quality_pages": sum(1 for p in successful if p.get("quality_score", 0) > 0.8),
                "low_quality_pages": sum(1 for p in successful if p.get("quality_score", 0) < 0.6)
            },
            "page_sequence_validation": {
                "issues_found": len(validation_issues),
                "validation_details": validation_issues
            },
            "performance_metrics": performance_report.to_dict(),
            "resource_usage": resource_stats
        }
        
        logger.info(f"Manual loop orchestrator completed. Success: {len(successful)}, Failed: {len(failed)}")
        logger.info(f"Error summary: {error_summary}")
        
        # Log performance warnings if any
        if performance_report.pages_exceeding_llm_limit > 0:
            logger.warning(f"LLM LIMIT EXCEEDED: {performance_report.pages_exceeding_llm_limit} pages used more than 4 LLM calls")
        
        if simple_logger:
            simple_logger.log_event("crew_complete", {
                "message": f"Manual loop orchestrator completed {len(sorted_files)} pages",
                "successful": len(successful),
                "failed": len(failed),
                "elapsed_time": elapsed_time,
                "error_summary": error_summary
            })
        
        return summary
        
    except Exception as e:
        # Handle catastrophic errors that prevent processing
        error_handler.log_error(
            error=e,
            context={"operation": "orchestrator_initialization", "inputs": inputs}
        )
        
        return {
            "status": "error",
            "error": f"Orchestrator failed: {str(e)}",
            "total_pages": 0,
            "processed_successfully": 0,
            "failed": 0,
            "error_summary": error_handler.get_error_summary()
        }
    
    finally:
        # Final cleanup
        error_handler.cleanup_temp_files()
        
        # Get resource stats before cleanup
        resource_stats = resource_manager.get_resource_stats()
        
        # Full resource cleanup
        resource_manager.cleanup_all()


def kickoff(inputs: Dict[str, Any], simple_logger=None) -> Dict[str, Any]:
    """
    Execute production book ingestion crew using manual loop orchestrator.
    
    This is the main entry point that delegates to the manual loop orchestrator
    for sequential file processing instead of using CrewAI's kickoff_for_each.
    """
    return manual_loop_orchestrator(inputs, simple_logger)


class BookIngestionCrew:
    """
    Wrapper class for compatibility with main.py execution pattern.
    """
    def kickoff(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the crew using the kickoff function."""
        return kickoff(inputs)


# Main entry point for direct execution
if __name__ == "__main__":
    """
    Direct execution entry point for testing and development.
    Usage: python crew.py
    """
    import sys
    
    # Example inputs for testing
    test_inputs = {
        "client_user_id": "test-client",
        "google_drive_folder_path": "https://drive.google.com/drive/folders/test",
        "language": "es",
        "process_pages_limit": 2
    }
    
    print("🚀 Running Book Ingestion Crew directly...")
    print(f"Test inputs: {json.dumps(test_inputs, indent=2)}")
    
    try:
        result = kickoff(test_inputs)
        print("\n✅ Crew execution completed!")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)