"""Synchronous Database Storage Tool for Book Ingestion."""
import logging
import json
import os
from typing import Any, Type
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from sparkjar_shared.database.models import BookIngestions

logger = logging.getLogger(__name__)


class SyncDBStorageToolSchema(BaseModel):
    """Input schema for SyncDBStorageTool - accepts parameters directly."""
    client_user_id: str = Field(description="Client user ID")
    book_key: str = Field(description="Book key identifier")
    page_number: int = Field(description="Page number")
    file_name: str = Field(description="File name")
    language_code: str = Field(description="Language code")
    page_text: str = Field(description="Transcribed text from OCR")
    ocr_metadata: dict = Field(default={}, description="OCR metadata")


class SyncDBStorageTool(BaseTool):
    name: str = "sync_db_storage"
    description: str = "Store book page to database using synchronous operations."
    args_schema: Type[BaseModel] = SyncDBStorageToolSchema
    
    def _run(self, **kwargs) -> str:
        """Execute storage with direct parameters."""
        try:
            # Use direct database URL from environment
            database_url = os.getenv('DATABASE_URL_DIRECT')
            if not database_url:
                return json.dumps({"success": False, "error": "DATABASE_URL_DIRECT not configured"})
                
            # Convert asyncpg URL to psycopg2 for sync
            sync_url = database_url.replace('postgresql+asyncpg://', 'postgresql://')
            engine = create_engine(sync_url)
            Session = sessionmaker(bind=engine)
            
            try:
                with Session() as session:
                    # Store page directly
                    page = BookIngestions(
                        book_key=kwargs['book_key'],
                        page_number=kwargs['page_number'],
                        file_name=kwargs['file_name'],
                        language_code=kwargs['language_code'],
                        version=kwargs.get('version', 'original'),
                        page_text=kwargs['page_text'],
                        ocr_metadata=kwargs.get('ocr_metadata', {})
                    )
                    session.add(page)
                    session.commit()
                    
                    # Get the page ID
                    page_id = str(page.id)
                    
                    return json.dumps({
                        "success": True,
                        "page_id": page_id,
                        "page_number": page.page_number
                    })
            finally:
                engine.dispose()
                
        except Exception as e:
            logger.error(f"Storage error: {e}")
            return json.dumps({"success": False, "error": str(e)})