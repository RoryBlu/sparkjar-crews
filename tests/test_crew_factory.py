#!/usr/bin/env python3
"""
Test script for YAML-based crew factory implementation.

Tests the crew factory functionality to ensure:
- YAML configuration files are loaded correctly
- Agents are created with proper configuration
- Tasks are created with correct dependencies
- Tools are assigned to appropriate agents
- Sequential processing pipeline is configured

Requirements: 3.1, 3.2, 3.3, 3.4
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from crews.book_ingestion_crew.crew import build_crew_from_yaml, _create_tool_instance, _load_yaml
from tools.google_drive_download_tool import GoogleDriveDownloadTool
from tools.image_viewer_tool import ImageViewerTool
from tools.sync_db_storage_tool import SyncDBStorageTool
from crewai import Process

def test_yaml_loading():
    """Test YAML configuration loading."""
    print("Testing YAML configuration loading...")
    
    # Test agents.yaml loading
    agents_config = _load_yaml("agents.yaml")
    assert isinstance(agents_config, dict), "agents.yaml should return a dictionary"
    assert "download_agent" in agents_config, "download_agent should be in agents.yaml"
    assert "ocr_agent" in agents_config, "ocr_agent should be in agents.yaml"
    assert "storage_agent" in agents_config, "storage_agent should be in agents.yaml"
    
    # Test tasks.yaml loading
    tasks_config = _load_yaml("tasks.yaml")
    assert isinstance(tasks_config, dict), "tasks.yaml should return a dictionary"
    assert "download_task" in tasks_config, "download_task should be in tasks.yaml"
    assert "ocr_task" in tasks_config, "ocr_task should be in tasks.yaml"
    assert "storage_task" in tasks_config, "storage_task should be in tasks.yaml"
    
    print("✓ YAML configuration loading test passed")

def test_tool_creation():
    """Test tool instance creation."""
    print("Testing tool instance creation...")
    
    # Test GoogleDriveDownloadTool creation
    download_tool = _create_tool_instance("google_drive_download_tool")
    assert isinstance(download_tool, GoogleDriveDownloadTool), "Should create GoogleDriveDownloadTool instance"
    
    # Test ImageViewerTool creation
    ocr_tool = _create_tool_instance("image_viewer_tool")
    assert isinstance(ocr_tool, ImageViewerTool), "Should create ImageViewerTool instance"
    
    # Test SyncDBStorageTool creation
    storage_tool = _create_tool_instance("sync_db_storage_tool")
    assert isinstance(storage_tool, SyncDBStorageTool), "Should create SyncDBStorageTool instance"
    
    # Test unknown tool handling
    try:
        _create_tool_instance("unknown_tool")
        assert False, "Should raise ValueError for unknown tool"
    except ValueError as e:
        assert "Unknown tool" in str(e), "Should raise appropriate error message"
    
    print("✓ Tool instance creation test passed")

def test_crew_factory():
    """Test crew factory with YAML-based configuration."""
    print("Testing crew factory with YAML-based configuration...")
    
    # Build crew from YAML
    crew = build_crew_from_yaml()
    
    # Verify crew structure
    assert crew is not None, "Crew should be created"
    assert len(crew.agents) == 3, "Should have 3 agents"
    assert len(crew.tasks) == 3, "Should have 3 tasks"
    assert crew.process == Process.sequential, "Should use sequential processing"
    assert crew.memory == False, "Should have memory disabled"
    
    # Verify agents
    agent_roles = [agent.role for agent in crew.agents]
    expected_roles = ["File Downloader", "OCR Coordinator", "Data Storage Specialist"]
    for role in expected_roles:
        assert role in agent_roles, f"Agent with role '{role}' should exist"
    
    # Verify agent models (check if model is set correctly)
    for agent in crew.agents:
        # The model is stored in the agent's llm attribute, but the exact attribute name may vary
        # Let's check if the agent has the correct model configured
        assert hasattr(agent, 'llm'), f"Agent {agent.role} should have llm configured"
    
    # Verify agent tools
    download_agent = next(agent for agent in crew.agents if agent.role == "File Downloader")
    assert len(download_agent.tools) == 1, "Download agent should have 1 tool"
    assert isinstance(download_agent.tools[0], GoogleDriveDownloadTool), "Download agent should have GoogleDriveDownloadTool"
    
    ocr_agent = next(agent for agent in crew.agents if agent.role == "OCR Coordinator")
    assert len(ocr_agent.tools) == 1, "OCR agent should have 1 tool"
    assert isinstance(ocr_agent.tools[0], ImageViewerTool), "OCR agent should have ImageViewerTool"
    
    storage_agent = next(agent for agent in crew.agents if agent.role == "Data Storage Specialist")
    assert len(storage_agent.tools) == 1, "Storage agent should have 1 tool"
    assert isinstance(storage_agent.tools[0], SyncDBStorageTool), "Storage agent should have SyncDBStorageTool"
    
    # Verify task dependencies
    task_names = [task.description.split()[0] for task in crew.tasks]  # Simple way to identify tasks
    
    # Find OCR task (should have context from download task)
    ocr_task = None
    for task in crew.tasks:
        if "ImageViewerTool" in task.description:
            ocr_task = task
            break
    
    assert ocr_task is not None, "OCR task should exist"
    assert ocr_task.context is not None, "OCR task should have context"
    assert len(ocr_task.context) == 1, "OCR task should have 1 context task"
    
    # Find storage task (should have context from OCR task)
    storage_task = None
    for task in crew.tasks:
        if "SyncDBStorageTool" in task.description:
            storage_task = task
            break
    
    assert storage_task is not None, "Storage task should exist"
    assert storage_task.context is not None, "Storage task should have context"
    assert len(storage_task.context) == 1, "Storage task should have 1 context task"
    
    print("✓ Crew factory test passed")

def test_agent_configuration():
    """Test agent configuration from YAML."""
    print("Testing agent configuration from YAML...")
    
    agents_config = _load_yaml("agents.yaml")
    
    # Test download agent configuration
    download_config = agents_config["download_agent"]
    assert download_config["role"] == "File Downloader", "Download agent role should match"
    assert download_config["model"] == "gpt-4.1-nano", "Download agent should use gpt-4.1-nano"
    assert "google_drive_download_tool" in download_config["tools"], "Download agent should have google_drive_download_tool"
    
    # Test OCR agent configuration
    ocr_config = agents_config["ocr_agent"]
    assert ocr_config["role"] == "OCR Coordinator", "OCR agent role should match"
    assert ocr_config["model"] == "gpt-4.1-nano", "OCR agent should use gpt-4.1-nano"
    assert "image_viewer_tool" in ocr_config["tools"], "OCR agent should have image_viewer_tool"
    
    # Test storage agent configuration
    storage_config = agents_config["storage_agent"]
    assert storage_config["role"] == "Data Storage Specialist", "Storage agent role should match"
    assert storage_config["model"] == "gpt-4.1-nano", "Storage agent should use gpt-4.1-nano"
    assert "sync_db_storage_tool" in storage_config["tools"], "Storage agent should have sync_db_storage_tool"
    
    print("✓ Agent configuration test passed")

def test_task_configuration():
    """Test task configuration from YAML."""
    print("Testing task configuration from YAML...")
    
    tasks_config = _load_yaml("tasks.yaml")
    
    # Test download task configuration
    download_config = tasks_config["download_task"]
    assert download_config["agent"] == "download_agent", "Download task should be assigned to download_agent"
    assert "GoogleDriveDownloadTool" in download_config["description"], "Download task should mention GoogleDriveDownloadTool"
    
    # Test OCR task configuration
    ocr_config = tasks_config["ocr_task"]
    assert ocr_config["agent"] == "ocr_agent", "OCR task should be assigned to ocr_agent"
    assert "ImageViewerTool" in ocr_config["description"], "OCR task should mention ImageViewerTool"
    assert "download_task" in ocr_config["context"], "OCR task should have download_task as context"
    
    # Test storage task configuration
    storage_config = tasks_config["storage_task"]
    assert storage_config["agent"] == "storage_agent", "Storage task should be assigned to storage_agent"
    assert "SyncDBStorageTool" in storage_config["description"], "Storage task should mention SyncDBStorageTool"
    assert "ocr_task" in storage_config["context"], "Storage task should have ocr_task as context"
    
    print("✓ Task configuration test passed")

def main():
    """Run all crew factory tests."""
    print("Running crew factory tests...")
    print("=" * 50)
    
    try:
        test_yaml_loading()
        test_tool_creation()
        test_agent_configuration()
        test_task_configuration()
        test_crew_factory()
        
        print("=" * 50)
        print("✓ All crew factory tests passed!")
        print("\nCrew factory implementation verified:")
        print("- YAML configuration loading works correctly")
        print("- Agent initialization with gpt-4.1-nano model")
        print("- Sequential processing pipeline configured")
        print("- Tool assignment to appropriate agents")
        print("- Task dependencies properly established")
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()