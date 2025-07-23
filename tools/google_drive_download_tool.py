"""Google Drive Download Tool - downloads a single file by ID."""
import os
import json
import tempfile
from pathlib import Path
from typing import Type
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from tools.google_drive_tool import GoogleDriveTool


class GoogleDriveDownloadInput(BaseModel):
    """Input schema for downloading a single file."""
    file_id: str = Field(description="Google Drive file ID to download")
    file_name: str = Field(description="Name of the file for saving locally")
    client_user_id: str = Field(description="Client user ID for credentials")


class GoogleDriveDownloadTool(BaseTool):
    """Download a single file from Google Drive."""
    
    name: str = "google_drive_download"
    description: str = "Download a single file from Google Drive by file ID"
    args_schema: Type[BaseModel] = GoogleDriveDownloadInput
    
    def _run(self, file_id: str, file_name: str, client_user_id: str) -> str:
        """Download a single file and return the local path."""
        try:
            # Create temp directory for this download
            temp_dir = Path(tempfile.mkdtemp(prefix="book_page_"))
            
            # Use the existing GoogleDriveTool's download functionality
            drive_tool = GoogleDriveTool()
            service = drive_tool._get_service(client_user_id, readonly=True)
            
            # Download the file to our temp directory
            drive_tool._temp_dir = temp_dir  # Set the temp directory
            local_path = drive_tool._download_file(service, file_id, file_name)
            
            return json.dumps({
                "success": True,
                "local_path": local_path,
                "file_name": file_name
            })
            
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": str(e)
            })