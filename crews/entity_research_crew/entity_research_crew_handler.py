"""
Entity Research Crew Handler - Researches entities using web search and creates comprehensive memory profiles.
"""

import logging
from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime

from sparkjar_shared.crews import BaseCrewHandler
from .crew import build_crew

logger = logging.getLogger(__name__)


class EntityResearchCrewHandler(BaseCrewHandler):
    """
    Handler for the Entity Research Crew that researches entities
    and creates structured memory profiles.
    
    This crew performs web research on entities (people, companies, topics)
    and stores the findings as memories.
    """
    
    def __init__(self, job_id: Optional[UUID] = None):
        """Initialize the Entity Research Crew Handler."""
        super().__init__(job_id)
        self.crew_name = "entity_research_crew"
        
    async def execute(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the entity research crew to research an entity and create memories.
        
        Args:
            request_data: Dictionary containing:
                - client_user_id: UUID of the client
                - actor_type: Type of actor (synth, human, etc.)
                - actor_id: UUID of the actor
                - entity_name: Name of the entity to research
                - entity_domain: Domain/category of the entity (person, company, technology, etc.)
                - research_depth: Optional depth of research (basic, detailed, comprehensive)
                
        Returns:
            Dictionary containing:
                - status: Execution status
                - entity_profile: Structured profile of the researched entity
                - memories_created: List of memories created
                - sources: List of sources used
                - error: Error message if any
        """
        try:
            # Log execution start
            self.log_execution_start(request_data)
            
            # Validate required fields
            required_fields = ["client_user_id", "actor_type", "actor_id", "entity_name", "entity_domain"]
            missing_fields = [field for field in required_fields if field not in request_data]
            
            if missing_fields:
                return {
                    "status": "failed",
                    "error": f"Missing required fields: {', '.join(missing_fields)}",
                    "entity_profile": {},
                    "memories_created": [],
                    "sources": []
                }
                
            # Extract parameters
            client_user_id = request_data["client_user_id"]
            actor_type = request_data["actor_type"]
            actor_id = request_data["actor_id"]
            entity_name = request_data["entity_name"]
            entity_domain = request_data["entity_domain"]
            research_depth = request_data.get("research_depth", "detailed")
            
            # Validate entity_name
            if not entity_name or not isinstance(entity_name, str) or not entity_name.strip():
                return {
                    "status": "failed",
                    "error": "entity_name must be a non-empty string",
                    "entity_profile": {},
                    "memories_created": [],
                    "sources": []
                }
                
            # Build the crew
            logger.info(f"Building Entity Research Crew for entity: {entity_name}")
            crew = build_crew()
            
            # Prepare inputs
            crew_inputs = {
                "entity_name": entity_name.strip(),
                "entity_domain": entity_domain,
                "research_depth": research_depth,
                "client_user_id": client_user_id,
                "actor_type": actor_type,
                "actor_id": actor_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Execute the crew with logging
            logger.info(f"Researching entity: {entity_name} (domain: {entity_domain})")
            result = await self.execute_crew_with_logging(
                lambda: crew.kickoff(inputs=crew_inputs)
            )
            
            # Parse and structure the results
            research_results = self._parse_crew_results(result)
            
            # Save crew events
            await self.save_crew_events()
            
            # Log execution complete
            self.log_execution_complete(research_results)
            
            logger.info(f"Entity research completed: {research_results.get('summary', '')}")
            
            return {
                "status": "completed",
                "entity_profile": research_results.get("entity_profile", {}),
                "memories_created": research_results.get("memories_created", []),
                "sources": research_results.get("sources", []),
                "research_metadata": {
                    "entity_name": entity_name,
                    "entity_domain": entity_domain,
                    "research_depth": research_depth,
                    "execution_time": datetime.utcnow().isoformat(),
                    "summary": research_results.get("summary", "")
                }
            }
            
        except Exception as e:
            logger.error(f"Error executing Entity Research Crew: {str(e)}", exc_info=True)
            self.log_execution_error(e)
            return {
                "status": "failed",
                "error": str(e),
                "entity_profile": {},
                "memories_created": [],
                "sources": []
            }
            
    def _parse_crew_results(self, result: Any) -> Dict[str, Any]:
        """
        Parse the crew execution results into structured format.
        
        Args:
            result: Raw crew execution result
            
        Returns:
            Structured research results
        """
        # Default structure
        research_results = {
            "entity_profile": {},
            "memories_created": [],
            "sources": [],
            "summary": ""
        }
        
        try:
            # Extract results based on crew output format
            if hasattr(result, 'output'):
                output = result.output
            else:
                output = str(result)
                
            logger.debug(f"Raw crew output: {output[:500]}...")
            
            # Parse the output to extract entity profile
            # The final task outputs a structured entity profile
            output_str = str(output)
            
            # Extract basic profile information
            if "entity profile" in output_str.lower():
                research_results["entity_profile"] = {
                    "name": self._extract_field(output_str, "name"),
                    "type": self._extract_field(output_str, "type"),
                    "description": self._extract_field(output_str, "description"),
                    "key_facts": self._extract_list(output_str, "key facts"),
                    "related_entities": self._extract_list(output_str, "related entities")
                }
            
            # Count memories created
            memories_count = output_str.lower().count("memory created") + output_str.lower().count("stored memory")
            research_results["memories_created"] = [f"memory_{i+1}" for i in range(memories_count)]
            
            # Extract sources
            if "sources:" in output_str.lower():
                sources_section = output_str.split("sources:")[1].split("\n\n")[0]
                sources = [s.strip() for s in sources_section.split("\n") if s.strip()]
                research_results["sources"] = sources[:10]  # Limit to top 10 sources
            
            # Generate summary
            if research_results["entity_profile"]:
                research_results["summary"] = f"Successfully researched {research_results['entity_profile'].get('name', 'entity')}: {len(research_results['memories_created'])} memories created from {len(research_results['sources'])} sources"
            else:
                research_results["summary"] = "Entity research completed with limited results"
            
        except Exception as e:
            logger.error(f"Error parsing crew results: {e}", exc_info=True)
            research_results["summary"] = "Entity research completed with parsing errors"
            
        return research_results
    
    def _extract_field(self, text: str, field_name: str) -> str:
        """Extract a field value from text."""
        try:
            pattern = f"{field_name}:(.+?)(?:\n|$)"
            import re
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        except:
            pass
        return ""
    
    def _extract_list(self, text: str, list_name: str) -> list:
        """Extract a list from text."""
        try:
            pattern = f"{list_name}:(.+?)(?:\n\n|$)"
            import re
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                items = match.group(1).strip().split("\n")
                return [item.strip("- •").strip() for item in items if item.strip()]
        except:
            pass
        return []