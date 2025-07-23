"""
Book Ingestion Crew Handler
Implements the BaseCrewHandler interface for book ingestion operations.
"""

import logging
from typing import Dict, Any
from uuid import UUID
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

from crews.base import BaseCrewHandler
from sparkjar_shared.services.schema_validator import BaseSchemaValidator
from .crew import kickoff

logger = logging.getLogger(__name__)

class BookIngestionCrewHandler(BaseCrewHandler):
    """
    Handler for book ingestion crew operations.
    This is a minimal implementation for testing the crew handler pattern.
    """
    
    def __init__(self, job_id: UUID = None):
        """Initialize the book ingestion crew handler."""
        super().__init__(job_id)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("BookIngestionCrewHandler initialized")
        
        # Initialize database session for schema validation
        database_url = os.getenv('DATABASE_URL_DIRECT')
        if database_url:
            # Convert asyncpg URL to psycopg2 for sync
            sync_url = database_url.replace('postgresql+asyncpg://', 'postgresql://')
            engine = create_engine(sync_url)
            Session = sessionmaker(bind=engine)
            self.db_session = Session()
            self.schema_validator = BaseSchemaValidator(self.db_session)
            self.schema_validator.enable_cache(True)
        else:
            self.db_session = None
            self.schema_validator = None
            self.logger.warning("No DATABASE_URL_DIRECT found - schema validation disabled")
    
    async def execute(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the book ingestion crew with the provided request data.
        
        Args:
            request_data: Job request data including all parameters
            
        Returns:
            Dictionary containing execution results
            
        Raises:
            Exception: If execution fails
        """
        try:
            # Log execution start
            self.log_execution_start(request_data)
            
            # Validate request data against schema
            if self.schema_validator:
                validation_result = self.schema_validator.validate_data(
                    data=request_data,
                    schema_name="book_ingestion_crew",
                    object_type="crew_context"
                )
                
                if not validation_result.valid:
                    error_msg = f"Schema validation failed: {', '.join(validation_result.errors)}"
                    self.logger.error(error_msg)
                    raise ValueError(error_msg)
                
                self.logger.info(f"Schema validation passed using schema: {validation_result.schema_used}")
            else:
                self.logger.warning("Schema validator not available - skipping validation")
            
            # Add job_id to the request data for the crew
            crew_inputs = request_data.copy()
            crew_inputs['job_id'] = str(self.job_id) if self.job_id else 'unknown'
            
            self.logger.info(f"Executing book ingestion crew with inputs: {crew_inputs}")
            
            # Execute the crew with full logging capture
            # This will capture all CrewAI logs and agent interactions
            result = await self.execute_crew_with_logging(
                kickoff,  # The crew kickoff function
                crew_inputs,  # Pass inputs as first argument
                logger=self.simple_logger  # Pass simple logger for structured events
            )
            
            self.logger.info(f"Book ingestion crew execution completed: {result}")
            
            # Log execution complete
            self.log_execution_complete(result)
            
            # Save all collected events to database
            await self.save_crew_events()
            
            return result
            
        except Exception as e:
            self.logger.error(f"Book ingestion crew execution failed: {str(e)}", exc_info=True)
            self.log_execution_error(e)
            raise
    
    def validate_request(self, request_data: Dict[str, Any]) -> bool:
        """
        Validate the request data before execution using Pydantic schema.
        
        This method provides comprehensive input validation using the Pydantic model
        in addition to the database schema validation in execute() method.
        
        Args:
            request_data: Request data to validate
            
        Returns:
            True if valid, raises Exception if invalid
        """
        # First, call parent validation for required fields
        super().validate_request(request_data)
        
        # Use Pydantic validation for comprehensive input validation
        from .schema import validate_book_ingestion_input
        
        validation_result = validate_book_ingestion_input(request_data)
        
        if not validation_result.valid:
            # Create detailed error message from validation errors
            error_details = []
            for error in validation_result.errors:
                error_details.append(f"{error.field}: {error.message}")
            
            error_message = f"Input validation failed: {'; '.join(error_details)}"
            self.logger.error(error_message)
            raise ValueError(error_message)
        
        # Log successful validation with any warnings
        if validation_result.warnings:
            for warning in validation_result.warnings:
                self.logger.warning(f"Validation warning: {warning}")
        
        self.logger.info("Pydantic input validation successful")
        return True
    
    async def cleanup(self):
        """
        Cleanup resources after job execution.
        
        This includes:
        - Closing database sessions
        - Cleaning up temporary files
        - Releasing any held resources
        """
        try:
            if self.db_session:
                self.db_session.close()
                self.logger.info("Database session closed")
                
            # Note: The ResourceManager cleanup is handled within the crew execution
            # If we had a persistent resource manager, we would clean it up here
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    def get_job_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about this job type.
        
        Returns:
            Dictionary with job type metadata
        """
        return {
            "handler_class": self.__class__.__name__,
            "description": "Handles book ingestion operations including OCR, parsing, and storage",
            "crew_type": "book_ingestion_crew",
            "version": "2.0.0",
            "capabilities": [
                "multi_pass_ocr",
                "gpt4o_vision",
                "sequential_thinking",
                "database_storage",
                "embedding_generation",
                "page_by_page_processing",
                "todo_tracking",
                "context_aware_ocr"
            ]
        }