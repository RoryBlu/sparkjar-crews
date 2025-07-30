"""
Wrapper tools for Memory Maker Crew to simplify memory operations.
These tools handle the JSON formatting required by the hierarchical memory tool.
"""

import json
from typing import Dict, Any, List, Optional
from crewai.tools import tool


def create_memory_wrapper_tools(memory_tool) -> List:
    """
    Create wrapper tool functions for the memory tool.
    Returns a list of tool functions that handle JSON formatting.
    """
    
    @tool
    def create_memory_entity(name: str, entity_type: str, metadata: str = "{}") -> str:
        """
        Create a new memory entity.
        
        Args:
            name: Unique name for the entity
            entity_type: Type of entity (policy, procedure, person, project, etc.)
            metadata: JSON string of metadata (default: "{}")
            
        Returns:
            Result message from the memory service
        """
        try:
            metadata_dict = json.loads(metadata) if metadata != "{}" else {}
        except:
            metadata_dict = {}
            
        query = json.dumps({
            "action": "create_entity",
            "params": {
                "name": name,
                "entity_type": entity_type,
                "metadata": metadata_dict
            }
        })
        
        return memory_tool._run(query)
    
    @tool
    def add_memory_observation(entity_name: str, observation: str, 
                              observation_type: str = "general", 
                              source: str = "memory_maker_crew") -> str:
        """
        Add an observation to an existing entity.
        
        Args:
            entity_name: Name of the entity to add observation to
            observation: The observation content
            observation_type: Type of observation (general, policy_content, fact, skill, etc.)
            source: Source of the observation
            
        Returns:
            Result message from the memory service
        """
        query = json.dumps({
            "action": "add_observation",
            "params": {
                "entity_name": entity_name,
                "observation": observation,
                "observation_type": observation_type,
                "source": source
            }
        })
        
        return memory_tool._run(query)
    
    @tool
    def create_memory_relationship(from_entity: str, to_entity: str, 
                                  relationship_type: str) -> str:
        """
        Create a relationship between two entities.
        
        Args:
            from_entity: Name of the source entity
            to_entity: Name of the target entity
            relationship_type: Type of relationship (manages, reports_to, contains, etc.)
            
        Returns:
            Result message from the memory service
        """
        query = json.dumps({
            "action": "create_relationship",
            "params": {
                "from_entity_name": from_entity,
                "to_entity_name": to_entity,
                "relationship_type": relationship_type,
                "metadata": {}
            }
        })
        
        return memory_tool._run(query)
    
    @tool
    def search_memories(query_text: str, entity_type: str = "", 
                       include_hierarchy: bool = True, limit: int = 10) -> str:
        """
        Search for entities in memory.
        
        Args:
            query_text: Search query
            entity_type: Optional filter by entity type (empty string for all types)
            include_hierarchy: Whether to include inherited memories (default: True)
            limit: Maximum number of results
            
        Returns:
            Search results from the memory service
        """
        params = {
            "query": query_text,
            "include_hierarchy": include_hierarchy,
            "limit": limit
        }
        
        if entity_type:
            params["entity_type"] = entity_type
        
        query = json.dumps({
            "action": "search_entities",
            "params": params
        })
        
        return memory_tool._run(query)
    
    @tool
    def get_memory_entity(entity_name: str, include_hierarchy: bool = True) -> str:
        """
        Get details of a specific entity.
        
        Args:
            entity_name: Name of the entity to retrieve
            include_hierarchy: Whether to check inherited contexts
            
        Returns:
            Entity details from the memory service
        """
        query = json.dumps({
            "action": "get_entity",
            "params": {
                "entity_name": entity_name,
                "include_hierarchy": include_hierarchy
            }
        })
        
        return memory_tool._run(query)
    
    # Return the list of tools
    return [
        create_memory_entity,
        add_memory_observation,
        create_memory_relationship,
        search_memories,
        get_memory_entity
    ]