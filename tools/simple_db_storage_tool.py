"""Simple Database Storage Tool for Book Ingestion."""
import logging
import json
from typing import Any, Type
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import os
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from sparkjar_shared.database.models import ClientUsers, ClientSecrets, BookIngestions

logger = logging.getLogger(__name__)


class SimpleDBStorageToolSchema(BaseModel):
    """Input schema for SimpleDBStorageTool - accepts parameters directly."""
    client_user_id: str = Field(description="Client user ID")
    book_key: str = Field(description="Book key identifier")
    page_number: int = Field(description="Page number")
    file_name: str = Field(description="File name")
    language_code: str = Field(description="Language code")
    page_text: str = Field(description="Transcribed text from OCR")
    ocr_metadata: dict = Field(default={}, description="OCR metadata")


class SimpleDBStorageTool(BaseTool):
    name: str = "simple_db_storage"
    description: str = "Store book page to database. Pass all parameters as a single JSON string."
    args_schema: Type[BaseModel] = SimpleDBStorageToolSchema
    
    def __init__(self):
        super().__init__()
        self._engine = None
    
    def _store_page(self, params: dict) -> dict:
        """Store page in database."""
        # Get client database URL
        from sparkjar_shared.database.connection import get_db_session
        
        async with get_db_session() as session:
            # Get user's client_id
            result = await session.execute(
                select(ClientUsers).filter_by(id=params['client_user_id'])
            )
            user = result.scalar_one_or_none()
            
            if not user:
                raise ValueError(f"User not found")
            
            # Get database URL
            secrets_result = await session.execute(
                select(ClientSecrets).filter_by(
                    client_id=user.clients_id,
                    secret_key="database_url"
                )
            )
            secret = secrets_result.scalar_one_or_none()
            
            if not secret:
                raise ValueError(f"Database URL not found")
            
            db_url = secret.secret_value
            if db_url.startswith("postgresql://"):
                db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        
        # Connect to client database
        engine = create_async_engine(db_url, echo=False)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        try:
            async with async_session() as session:
                # Check if page already exists
                existing = await session.execute(
                    select(BookIngestions).filter_by(
                        book_key=params['book_key'],
                        page_number=params['page_number'],
                        version=params.get('version', 'original')
                    )
                )
                page = existing.scalar_one_or_none()
                
                if page:
                    # Update existing
                    page.file_name = params['file_name']
                    page.page_text = params['page_text']
                    page.ocr_metadata = params.get('ocr_metadata', {})
                    page.updated_at = datetime.utcnow()
                else:
                    # Create new
                    page = BookIngestions(
                        book_key=params['book_key'],
                        page_number=params['page_number'],
                        file_name=params['file_name'],
                        language_code=params['language_code'],
                        version=params.get('version', 'original'),
                        page_text=params['page_text'],
                        ocr_metadata=params.get('ocr_metadata', {})
                    )
                    session.add(page)
                
                await session.commit()
                await session.refresh(page)
                
                return {
                    "success": True,
                    "page_id": str(page.id),
                    "page_number": page.page_number
                }
        finally:
            await engine.dispose()
    
    def _run(self, **kwargs) -> str:
        """Execute storage with direct parameters."""
        try:
            # CrewAI passes parameters directly as kwargs
            params = kwargs
            
            # Run async operation - handle nested event loops
            try:
                loop = asyncio.get_running_loop()
                # We're in an event loop, use run_coroutine_threadsafe
                import concurrent.futures
                import threading
                
                result = None
                exception = None
                
                def run_in_thread():
                    nonlocal result, exception
                    try:
                        # Create new event loop in thread
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        result = new_loop.run_until_complete(self._store_page(params))
                        new_loop.close()
                    except Exception as e:
                        exception = e
                
                thread = threading.Thread(target=run_in_thread)
                thread.start()
                thread.join()
                
                if exception:
                    raise exception
                    
                return json.dumps(result)
            except RuntimeError:
                # No event loop, can use asyncio.run
                result = asyncio.run(self._store_page(params))
                return json.dumps(result)
            
        except Exception as e:
            logger.error(f"Storage error: {e}")
            return json.dumps({"success": False, "error": str(e)})