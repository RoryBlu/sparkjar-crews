"""
Unit tests for Memory Maker Crew Request and Response Models.
"""

import pytest
from datetime import datetime
from uuid import UUID, uuid4
from pydantic import ValidationError

from ..models import (
    MemoryMakerRequest,
    MemoryEntity,
    MemoryObservation,
    MemoryRelationship,
    ProcessingMetadata,
    MemoryMakerError,
    MemoryProcessingResult,
    validate_actor_type_supported,
    validate_text_length,
    create_validation_error
)


class TestMemoryMakerRequest:
    """Test cases for MemoryMakerRequest model."""
    
    def test_valid_request_with_uuid(self):
        """Test valid request with UUID actor_id."""
        actor_id = uuid4()
        client_user_id = uuid4()
        
        request = MemoryMakerRequest(
            actor_type="client",
            actor_id=actor_id,
            client_user_id=client_user_id,
            text_content="This is test content for memory extraction."
        )
        
        assert request.actor_type == "client"
        assert request.actor_id == str(actor_id)
        assert request.client_user_id == str(client_user_id)
        assert request.text_content == "This is test content for memory extraction."
        assert request.metadata == {}
        assert request.extract_entities is True
        assert request.extract_relationships is True
        assert request.entity_types is None
    
    def test_valid_request_with_string_id(self):
        """Test valid request with string actor_id for synth_class."""
        request = MemoryMakerRequest(
            actor_type="synth_class",
            actor_id="24",
            client_user_id=str(uuid4()),
            text_content="Synth class content for testing."
        )
        
        assert request.actor_type == "synth_class"
        assert request.actor_id == "24"
        assert request.text_content == "Synth class content for testing."    def
 test_text_content_validation_empty(self):
        """Test validation error for empty text content."""
        with pytest.raises(ValidationError) as exc_info:
            MemoryMakerRequest(
                actor_type="client",
                actor_id=str(uuid4()),
                client_user_id=str(uuid4()),
                text_content=""
            )
        
        assert "text_content cannot be empty or whitespace only" in str(exc_info.value)
    
    def test_text_content_validation_whitespace(self):
        """Test validation error for whitespace-only text content."""
        with pytest.raises(ValidationError) as exc_info:
            MemoryMakerRequest(
                actor_type="client",
                actor_id=str(uuid4()),
                client_user_id=str(uuid4()),
                text_content="   \n\t   "
            )
        
        assert "text_content cannot be empty or whitespace only" in str(exc_info.value)
    
    def test_text_content_trimming(self):
        """Test that text content is properly trimmed."""
        request = MemoryMakerRequest(
            actor_type="client",
            actor_id=str(uuid4()),
            client_user_id=str(uuid4()),
            text_content="  \n  Test content with whitespace  \t  "
        )
        
        assert request.text_content == "Test content with whitespace"
    
    def test_invalid_actor_type(self):
        """Test validation error for invalid actor type."""
        with pytest.raises(ValidationError) as exc_info:
            MemoryMakerRequest(
                actor_type="invalid_type",
                actor_id=str(uuid4()),
                client_user_id=str(uuid4()),
                text_content="Test content"
            )
        
        assert "Input should be" in str(exc_info.value)
    
    def test_uuid_actor_id_validation_for_client(self):
        """Test UUID validation for client actor type."""
        with pytest.raises(ValidationError) as exc_info:
            MemoryMakerRequest(
                actor_type="client",
                actor_id="invalid-uuid",
                client_user_id=str(uuid4()),
                text_content="Test content"
            )
        
        assert "actor_id for client must be a valid UUID" in str(exc_info.value)
    
    def test_synth_class_string_id_allowed(self):
        """Test that synth_class allows string IDs."""
        request = MemoryMakerRequest(
            actor_type="synth_class",
            actor_id="24",
            client_user_id=str(uuid4()),
            text_content="Test content"
        )
        
        assert request.actor_id == "24"    def
 test_skill_module_uuid_allowed(self):
        """Test that skill_module allows UUID IDs."""
        skill_id = uuid4()
        request = MemoryMakerRequest(
            actor_type="skill_module",
            actor_id=skill_id,
            client_user_id=str(uuid4()),
            text_content="Test content"
        )
        
        assert request.actor_id == str(skill_id)
    
    def test_empty_id_validation(self):
        """Test validation error for empty ID."""
        with pytest.raises(ValidationError) as exc_info:
            MemoryMakerRequest(
                actor_type="synth_class",
                actor_id="",
                client_user_id=str(uuid4()),
                text_content="Test content"
            )
        
        assert "ID cannot be empty" in str(exc_info.value)
    
    def test_entity_types_validation_empty_list(self):
        """Test validation error for empty entity_types list."""
        with pytest.raises(ValidationError) as exc_info:
            MemoryMakerRequest(
                actor_type="client",
                actor_id=str(uuid4()),
                client_user_id=str(uuid4()),
                text_content="Test content",
                entity_types=[]
            )
        
        assert "entity_types cannot be an empty list" in str(exc_info.value)
    
    def test_entity_types_validation_empty_strings(self):
        """Test validation error for entity_types with only empty strings."""
        with pytest.raises(ValidationError) as exc_info:
            MemoryMakerRequest(
                actor_type="client",
                actor_id=str(uuid4()),
                client_user_id=str(uuid4()),
                text_content="Test content",
                entity_types=["", "  ", "\t"]
            )
        
        assert "entity_types cannot contain only empty strings" in str(exc_info.value)
    
    def test_entity_types_cleaning(self):
        """Test that entity_types are properly cleaned."""
        request = MemoryMakerRequest(
            actor_type="client",
            actor_id=str(uuid4()),
            client_user_id=str(uuid4()),
            text_content="Test content",
            entity_types=["policy", "  procedure  ", "policy", "organization"]
        )
        
        # Should remove duplicates and trim whitespace
        assert "policy" in request.entity_types
        assert "procedure" in request.entity_types
        assert "organization" in request.entity_types
        assert len([t for t in request.entity_types if t == "policy"]) == 1  # No duplicates  
  def test_optional_fields_defaults(self):
        """Test default values for optional fields."""
        request = MemoryMakerRequest(
            actor_type="client",
            actor_id=str(uuid4()),
            client_user_id=str(uuid4()),
            text_content="Test content"
        )
        
        assert request.metadata == {}
        assert request.extract_entities is True
        assert request.extract_relationships is True
        assert request.entity_types is None


class TestMemoryEntity:
    """Test cases for MemoryEntity model."""
    
    def test_valid_memory_entity(self):
        """Test valid memory entity creation."""
        entity = MemoryEntity(
            entity_name="Vervelyn Publishing",
            entity_type="organization",
            confidence_score=0.95,
            context_source="client",
            metadata={"industry": "publishing"}
        )
        
        assert entity.entity_name == "Vervelyn Publishing"
        assert entity.entity_type == "organization"
        assert entity.confidence_score == 0.95
        assert entity.context_source == "client"
        assert entity.metadata["industry"] == "publishing"
    
    def test_confidence_score_validation(self):
        """Test confidence score validation."""
        # Valid score
        entity = MemoryEntity(
            entity_name="Test Entity",
            entity_type="concept",
            confidence_score=0.5
        )
        assert entity.confidence_score == 0.5
        
        # Invalid score - too high
        with pytest.raises(ValidationError):
            MemoryEntity(
                entity_name="Test Entity",
                entity_type="concept",
                confidence_score=1.5
            )
        
        # Invalid score - negative
        with pytest.raises(ValidationError):
            MemoryEntity(
                entity_name="Test Entity",
                entity_type="concept",
                confidence_score=-0.1
            )class TestM
emoryProcessingResult:
    """Test cases for MemoryProcessingResult model."""
    
    def test_valid_processing_result(self):
        """Test valid processing result creation."""
        metadata = ProcessingMetadata(
            text_length=1000,
            entities_extracted=5,
            observations_created=10,
            relationships_created=3
        )
        
        result = MemoryProcessingResult(
            status="completed",
            processing_metadata=metadata,
            summary="Successfully processed corporate policy document"
        )
        
        assert result.status == "completed"
        assert result.processing_metadata.text_length == 1000
        assert result.summary == "Successfully processed corporate policy document"
        assert len(result.errors) == 0
    
    def test_status_consistency_validation_failed_without_errors(self):
        """Test validation error when status is failed but no errors provided."""
        metadata = ProcessingMetadata(text_length=1000)
        
        with pytest.raises(ValidationError) as exc_info:
            MemoryProcessingResult(
                status="failed",
                processing_metadata=metadata
            )
        
        assert "Failed status requires at least one error" in str(exc_info.value)
    
    def test_status_auto_correction_completed_with_errors(self):
        """Test automatic status correction from completed to partial when errors exist."""
        metadata = ProcessingMetadata(text_length=1000)
        error = MemoryMakerError(
            error_code="PARTIAL_FAILURE",
            error_message="Some entities could not be processed"
        )
        
        result = MemoryProcessingResult(
            status="completed",
            processing_metadata=metadata,
            errors=[error]
        )
        
        # Status should be automatically corrected to partial
        assert result.status == "partial" 
   def test_get_total_items_processed(self):
        """Test total items processed calculation."""
        metadata = ProcessingMetadata(text_length=1000)
        
        result = MemoryProcessingResult(
            status="completed",
            processing_metadata=metadata,
            entities_created=[
                MemoryEntity(entity_name="Entity1", entity_type="concept"),
                MemoryEntity(entity_name="Entity2", entity_type="policy")
            ],
            entities_updated=[
                MemoryEntity(entity_name="Entity3", entity_type="organization")
            ],
            observations_added=[
                MemoryObservation(observation_text="Observation1"),
                MemoryObservation(observation_text="Observation2")
            ],
            relationships_created=[
                MemoryRelationship(
                    source_entity="Entity1",
                    target_entity="Entity2",
                    relationship_type="related_to"
                )
            ]
        )
        
        # 2 created + 1 updated + 2 observations + 1 relationship = 6
        assert result.get_total_items_processed() == 6
    
    def test_has_errors(self):
        """Test error detection."""
        metadata = ProcessingMetadata(text_length=1000)
        
        # No errors
        result = MemoryProcessingResult(
            status="completed",
            processing_metadata=metadata
        )
        assert result.has_errors() is False
        
        # With errors
        error = MemoryMakerError(
            error_code="TEST_ERROR",
            error_message="Test error"
        )
        result.errors.append(error)
        assert result.has_errors() is True    def
 test_get_error_summary(self):
        """Test error summary generation."""
        metadata = ProcessingMetadata(text_length=1000)
        
        # No errors
        result = MemoryProcessingResult(
            status="completed",
            processing_metadata=metadata
        )
        assert result.get_error_summary() == "No errors"
        
        # With multiple errors
        errors = [
            MemoryMakerError(error_code="VALIDATION_ERROR", error_message="Error 1"),
            MemoryMakerError(error_code="VALIDATION_ERROR", error_message="Error 2"),
            MemoryMakerError(error_code="SERVICE_ERROR", error_message="Error 3")
        ]
        result.errors = errors
        
        summary = result.get_error_summary()
        assert "VALIDATION_ERROR: 2" in summary
        assert "SERVICE_ERROR: 1" in summary


class TestValidationHelpers:
    """Test cases for validation helper functions."""
    
    def test_validate_actor_type_supported(self):
        """Test actor type support validation."""
        supported_types = ["client", "synth", "synth_class", "skill_module"]
        
        assert validate_actor_type_supported("client", supported_types) is True
        assert validate_actor_type_supported("synth_class", supported_types) is True
        assert validate_actor_type_supported("invalid_type", supported_types) is False
    
    def test_validate_text_length(self):
        """Test text length validation."""
        # Valid length
        assert validate_text_length("Hello world", min_length=1, max_length=100) is True
        
        # Too short
        assert validate_text_length("", min_length=1, max_length=100) is False
        
        # Too long
        assert validate_text_length("x" * 101, min_length=1, max_length=100) is False
        
        # Whitespace only
        assert validate_text_length("   ", min_length=1, max_length=100) is False
    
    def test_create_validation_error(self):
        """Test validation error creation."""
        error = create_validation_error("text_content", "cannot be empty", "")
        
        assert error.error_code == "VALIDATION_ERROR"
        assert "Validation failed for text_content" in error.error_message
        assert error.error_details["field"] == "text_content"
        assert error.error_details["message"] == "cannot be empty"
        assert error.error_details["value"] == ""