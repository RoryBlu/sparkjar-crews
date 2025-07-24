"""
Memory Maker Crew Handler - Processes any text to extract and store memories.
"""

import logging
from typing import Dict, Any, List, Optional, Union
from uuid import UUID
from datetime import datetime

from crews.base import BaseCrewHandler
# from src.database.models import CrewJob  # Not needed in standalone
from .crew import MemoryMakerCrew

logger = logging.getLogger(__name__)


class MemoryMakerCrewHandler(BaseCrewHandler):
    """
    Handler for the Memory Maker Crew that analyzes any text content
    and extracts structured memories for storage.
    
    Supports various text types including:
    - Documents and articles
    - Conversations and transcripts
    - Emails and messages
    - Meeting notes
    - Research papers
    - Any unstructured text
    """
    
    def __init__(self):
        """Initialize the Memory Maker Crew Handler."""
        super().__init__()
        self.crew_name = "memory_maker_crew"
        
    async def execute(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the memory maker crew to process text and extract memories.
        
        Args:
            request_data: Dictionary containing:
                - client_user_id: UUID of the client
                - actor_type: Type of actor (synth, human, etc.)
                - actor_id: UUID of the actor
                - text_content: Text to analyze (string)
                - metadata: Optional metadata about the text source
                
        Returns:
            Dictionary containing:
                - status: Execution status
                - entities_created: List of created memory entities
                - entities_updated: List of updated memory entities
                - observations_added: List of new observations
                - relationships_created: List of new relationships
                - error: Error message if any
        """
        try:
            # Validate required fields
            required_fields = ["client_user_id", "actor_type", "actor_id", "text_content"]
            missing_fields = [field for field in required_fields if field not in request_data]
            
            if missing_fields:
                return {
                    "status": "failed",
                    "error": f"Missing required fields: {', '.join(missing_fields)}",
                    "entities_created": [],
                    "entities_updated": [],
                    "observations_added": [],
                    "relationships_created": []
                }
                
            # Extract parameters
            client_user_id = request_data["client_user_id"]
            actor_type = request_data["actor_type"]
            actor_id = request_data["actor_id"]
            text_content = request_data["text_content"]
            metadata = request_data.get("metadata", {})
            
            # Validate text content
            if not text_content or not isinstance(text_content, str) or not text_content.strip():
                return {
                    "status": "failed",
                    "error": "text_content must be a non-empty string",
                    "entities_created": [],
                    "entities_updated": [],
                    "observations_added": [],
                    "relationships_created": []
                }
                
            # Create the crew instance
            logger.info(f"Creating Memory Maker Crew for actor {actor_id}")
            crew = MemoryMakerCrew(
                client_user_id=client_user_id,
                actor_type=actor_type,
                actor_id=actor_id
            )
            
            # Process the text
            logger.info(f"Processing text content ({len(text_content)} characters)")
            
            # Add context to the inputs
            crew_inputs = {
                "text_content": text_content.strip(),
                "metadata": metadata,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Execute the crew
            result = crew.crew().kickoff(inputs=crew_inputs)
            
            # Parse and structure the results
            extraction_results = self._parse_crew_results(result)
            
            logger.info(f"Memory extraction completed: {extraction_results['summary']}")
            
            return {
                "status": "completed",
                "entities_created": extraction_results.get("entities_created", []),
                "entities_updated": extraction_results.get("entities_updated", []),
                "observations_added": extraction_results.get("observations_added", []),
                "relationships_created": extraction_results.get("relationships_created", []),
                "extraction_metadata": {
                    "text_length": len(text_content),
                    "extraction_time": datetime.utcnow().isoformat(),
                    "summary": extraction_results.get("summary", "")
                }
            }
            
        except Exception as e:
            logger.error(f"Error executing Memory Maker Crew: {str(e)}", exc_info=True)
            return {
                "status": "failed",
                "error": str(e),
                "entities_created": [],
                "entities_updated": [],
                "observations_added": [],
                "relationships_created": []
            }
            
        
    def _parse_crew_results(self, result: Any) -> Dict[str, Any]:
        """
        Parse the crew execution results into structured format.
        
        Args:
            result: Raw crew execution result
            
        Returns:
            Structured extraction results
        """
        # Default structure
        extraction_results = {
            "entities_created": [],
            "entities_updated": [],
            "observations_added": [],
            "relationships_created": [],
            "summary": ""
        }
        
        try:
            # Extract results based on crew output format
            if hasattr(result, 'output'):
                output = result.output
            else:
                output = str(result)
                
            logger.debug(f"Raw crew output: {output}")
            
            # The final task (store_memories) outputs a report of memory operations
            # Parse the output to extract the actual results
            output_str = str(output).lower()
            
            # Count entities created/updated
            entities_created = output_str.count("entity created") + output_str.count("created entity")
            entities_updated = output_str.count("entity updated") + output_str.count("updated entity")
            
            # Count observations and relationships
            observations_added = output_str.count("observation") + output_str.count("observations added")
            relationships_created = output_str.count("relationship created") + output_str.count("created relationship")
            
            # Extract summary
            if entities_created > 0 or entities_updated > 0:
                extraction_results["summary"] = f"Successfully processed text: {entities_created} entities created, {entities_updated} entities updated, {observations_added} observations added"
            else:
                extraction_results["summary"] = "Text processed but no memories extracted"
            
            # Since the crew doesn't return structured data, we'll populate counts
            # In a future iteration, we could parse the actual entity names from the output
            extraction_results["entities_created"] = [f"entity_{i+1}" for i in range(entities_created)]
            extraction_results["entities_updated"] = [f"updated_entity_{i+1}" for i in range(entities_updated)]
            extraction_results["observations_added"] = [f"observation_{i+1}" for i in range(observations_added)]
            extraction_results["relationships_created"] = [f"relationship_{i+1}" for i in range(relationships_created)]
            
        except Exception as e:
            logger.error(f"Error parsing crew results: {e}", exc_info=True)
            extraction_results["summary"] = "Memory extraction completed with parsing errors"
            
        return extraction_results