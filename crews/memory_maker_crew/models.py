"""
Memory Maker Crew Request and Response Models

This module provides Pydantic models for request validation and response formatting
for the Memory Maker Crew.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional, Literal, Union
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, field_validator, model_validator


class MemoryMakerRequest(BaseModel):
    """
    Request model for Memory Maker Crew execution.
    
    This model validates all input data for the Memory Maker Crew,
    ensuring proper actor context and text content validation.
    """
    
    # Actor Context
    actor_type: Literal["client", "synth", "human", "synth_class", "skill_module"] = Field(
        description="Type of actor for memory context"
    )
    
    actor_id: Union[UUID, str] = Field(
        description="Unique identifier for the actor"
    )
    
    client_user_id: Union[UUID, str] = Field(
        description="Client user identifier for context"
    )
    
    # Content
    text_content: str = Field(
        description="Text content to analyze and extract memories from"
    )
    
    # Optional metadata
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Optional metadata about the text source"
    )
    
    # Processing options
    extract_entities: bool = Field(
        default=True,
        description="Whether to extract entities from the text"
    )
    
    extract_relationships: bool = Field(
        default=True,
        description="Whether to extract relationships between entities"
    )
    
    entity_types: Optional[List[str]] = Field(
        default=None,
        description="Specific entity types to focus on (if None, uses defaults)"
    )
    
    @field_validator('text_content')
    @classmethod
    def validate_text_content(cls, v):
        """Validate text content is not empty or whitespace only."""
        if not v or not v.strip():
            raise ValueError('text_content cannot be empty or whitespace only')
        
        # Check length constraints
        stripped = v.strip()
        if len(stripped) < 1:
            raise ValueError('text_content cannot be empty or whitespace only')
        if len(stripped) > 100000:
            raise ValueError('text_content cannot exceed 100000 characters')
        
        return stripped
    
    @field_validator('actor_id', 'client_user_id')
    @classmethod
    def validate_ids(cls, v):
        """Validate and convert IDs to strings."""
        if isinstance(v, UUID):
            return str(v)
        elif isinstance(v, str):
            # Validate UUID format if string
            try:
                UUID(v)
                return v
            except ValueError:
                # For non-UUID strings (like synth_class "24"), allow them
                if v.strip():
                    return v.strip()
                raise ValueError('ID cannot be empty')
        else:
            raise ValueError('ID must be a UUID or string')
    
    @field_validator('entity_types')
    @classmethod
    def validate_entity_types(cls, v):
        """Validate entity types list."""
        if v is not None:
            if not isinstance(v, list):
                raise ValueError('entity_types must be a list')
            if not v:
                raise ValueError('entity_types cannot be an empty list (use None instead)')
            # Remove duplicates and empty strings
            v = [t.strip() for t in v if t and t.strip()]
            if not v:
                raise ValueError('entity_types cannot contain only empty strings')
        return v
    
    @model_validator(mode='after')
    def validate_actor_context(self):
        """Validate actor context consistency."""
        # For synth_class, actor_id can be a simple string like "24"
        if self.actor_type == "synth_class":
            # Allow simple string IDs for synth_class
            pass
        elif self.actor_type == "skill_module":
            # Allow UUID or string IDs for skill_module
            pass
        elif self.actor_type in ["client", "synth", "human"]:
            # These should have UUID format
            try:
                UUID(self.actor_id)
            except ValueError:
                raise ValueError(f'actor_id for {self.actor_type} must be a valid UUID')
        
        return self
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }
        validate_assignment = True


class MemoryEntity(BaseModel):
    """Model for a memory entity extracted from text."""
    
    entity_name: str = Field(description="Name of the entity")
    entity_type: str = Field(description="Type/category of the entity")
    confidence_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confidence score for entity extraction"
    )
    context_source: str = Field(
        default="own",
        description="Source context (own, synth_class, client, etc.)"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the entity"
    )


class MemoryObservation(BaseModel):
    """Model for a memory observation about an entity."""
    
    observation_text: str = Field(description="The observation content")
    observation_type: str = Field(
        default="general",
        description="Type of observation (general, attribute, behavior, etc.)"
    )
    confidence_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confidence score for observation"
    )
    source_context: str = Field(
        default="text_analysis",
        description="Context where this observation was made"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the observation"
    )


class MemoryRelationship(BaseModel):
    """Model for a relationship between memory entities."""
    
    source_entity: str = Field(description="Source entity name")
    target_entity: str = Field(description="Target entity name")
    relationship_type: str = Field(description="Type of relationship")
    relationship_strength: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Strength of the relationship"
    )
    bidirectional: bool = Field(
        default=False,
        description="Whether the relationship is bidirectional"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the relationship"
    )


class ProcessingMetadata(BaseModel):
    """Metadata about the memory processing operation."""
    
    processing_time_seconds: Optional[float] = Field(
        default=None,
        description="Time taken to process the request"
    )
    text_length: int = Field(description="Length of processed text")
    entities_extracted: int = Field(default=0, description="Number of entities extracted")
    observations_created: int = Field(default=0, description="Number of observations created")
    relationships_created: int = Field(default=0, description="Number of relationships created")
    processing_timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the processing occurred"
    )
    crew_execution_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique identifier for this crew execution"
    )


class MemoryMakerError(BaseModel):
    """Model for structured error responses."""
    
    error_code: str = Field(description="Error code for categorization")
    error_message: str = Field(description="Human-readable error message")
    error_details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional error details"
    )
    retry_after: Optional[int] = Field(
        default=None,
        description="Seconds to wait before retrying (if applicable)"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the error occurred"
    )


class MemoryProcessingResult(BaseModel):
    """Complete result of memory processing operation."""
    
    status: Literal["completed", "failed", "partial"] = Field(
        description="Overall status of the processing"
    )
    
    # Success data
    entities_created: List[MemoryEntity] = Field(
        default_factory=list,
        description="List of entities that were created"
    )
    
    entities_updated: List[MemoryEntity] = Field(
        default_factory=list,
        description="List of entities that were updated"
    )
    
    observations_added: List[MemoryObservation] = Field(
        default_factory=list,
        description="List of observations that were added"
    )
    
    relationships_created: List[MemoryRelationship] = Field(
        default_factory=list,
        description="List of relationships that were created"
    )
    
    # Processing metadata
    processing_metadata: ProcessingMetadata = Field(
        description="Metadata about the processing operation"
    )
    
    # Error information
    errors: List[MemoryMakerError] = Field(
        default_factory=list,
        description="List of errors that occurred during processing"
    )
    
    # Summary information
    summary: str = Field(
        default="",
        description="Human-readable summary of the processing results"
    )
    
    @model_validator(mode='after')
    def validate_status_consistency(self):
        """Validate that status is consistent with results."""
        if self.status == "failed" and not self.errors:
            raise ValueError("Failed status requires at least one error")
        
        if self.status == "completed" and self.errors:
            # If there are errors but status is completed, change to partial
            self.status = "partial"
        
        return self
    
    def get_total_items_processed(self) -> int:
        """Get total number of items processed."""
        return (
            len(self.entities_created) +
            len(self.entities_updated) +
            len(self.observations_added) +
            len(self.relationships_created)
        )
    
    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self.errors) > 0
    
    def get_error_summary(self) -> str:
        """Get a summary of all errors."""
        if not self.errors:
            return "No errors"
        
        error_counts = {}
        for error in self.errors:
            error_counts[error.error_code] = error_counts.get(error.error_code, 0) + 1
        
        return "; ".join([f"{code}: {count}" for code, count in error_counts.items()])


# Validation helper functions

def validate_actor_type_supported(actor_type: str, supported_types: List[str]) -> bool:
    """
    Validate that an actor type is supported.
    
    Args:
        actor_type: The actor type to validate
        supported_types: List of supported actor types
        
    Returns:
        True if supported, False otherwise
    """
    return actor_type in supported_types


def validate_text_length(text: str, min_length: int = 1, max_length: int = 100000) -> bool:
    """
    Validate text length constraints.
    
    Args:
        text: Text to validate
        min_length: Minimum allowed length
        max_length: Maximum allowed length
        
    Returns:
        True if valid, False otherwise
    """
    if not text:
        return False
    
    text_len = len(text.strip())
    return min_length <= text_len <= max_length


def create_validation_error(field_name: str, message: str, value: Any = None) -> MemoryMakerError:
    """
    Create a standardized validation error.
    
    Args:
        field_name: Name of the field that failed validation
        message: Error message
        value: The invalid value (optional)
        
    Returns:
        MemoryMakerError instance
    """
    return MemoryMakerError(
        error_code="VALIDATION_ERROR",
        error_message=f"Validation failed for {field_name}: {message}",
        error_details={
            "field": field_name,
            "message": message,
            "value": str(value) if value is not None else None
        }
    )