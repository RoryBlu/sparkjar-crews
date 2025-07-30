#!/usr/bin/env python3
"""
Direct test of MemoryMakerRequest and related models.
"""

import os
import sys
from uuid import uuid4

# Add the current directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'crews', 'memory_maker_crew'))

from models import (
    MemoryMakerRequest,
    MemoryEntity,
    MemoryProcessingResult,
    ProcessingMetadata,
    MemoryMakerError,
    validate_actor_type_supported,
    validate_text_length,
    create_validation_error
)


def test_memory_maker_request():
    """Test MemoryMakerRequest validation."""
    print("Testing MemoryMakerRequest...")
    
    # Valid request with UUID
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
    print("✓ Valid UUID request test passed")
    
    # Valid request with string ID for synth_class
    request2 = MemoryMakerRequest(
        actor_type="synth_class",
        actor_id="24",
        client_user_id=str(uuid4()),
        text_content="Synth class content for testing."
    )
    
    assert request2.actor_type == "synth_class"
    assert request2.actor_id == "24"
    print("✓ Valid string ID request test passed")
    
    # Test text content trimming
    request3 = MemoryMakerRequest(
        actor_type="client",
        actor_id=str(uuid4()),
        client_user_id=str(uuid4()),
        text_content="  \n  Test content with whitespace  \t  "
    )
    
    assert request3.text_content == "Test content with whitespace"
    print("✓ Text content trimming test passed")


def test_validation_errors():
    """Test validation error handling."""
    print("Testing validation errors...")
    
    # Test empty text content
    try:
        MemoryMakerRequest(
            actor_type="client",
            actor_id=str(uuid4()),
            client_user_id=str(uuid4()),
            text_content=""
        )
        assert False, "Should have raised validation error"
    except Exception as e:
        assert "text_content cannot be empty or whitespace only" in str(e)
        print("✓ Empty text content validation test passed")
    
    # Test invalid actor type
    try:
        MemoryMakerRequest(
            actor_type="invalid_type",
            actor_id=str(uuid4()),
            client_user_id=str(uuid4()),
            text_content="Test content"
        )
        assert False, "Should have raised validation error"
    except Exception as e:
        assert "Input should be" in str(e)
        print("✓ Invalid actor type validation test passed")
    
    # Test UUID validation for client
    try:
        MemoryMakerRequest(
            actor_type="client",
            actor_id="invalid-uuid",
            client_user_id=str(uuid4()),
            text_content="Test content"
        )
        assert False, "Should have raised validation error"
    except Exception as e:
        assert "actor_id for client must be a valid UUID" in str(e)
        print("✓ UUID validation test passed")


def test_memory_entity():
    """Test MemoryEntity model."""
    print("Testing MemoryEntity...")
    
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
    print("✓ MemoryEntity test passed")


def test_processing_result():
    """Test MemoryProcessingResult model."""
    print("Testing MemoryProcessingResult...")
    
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
    print("✓ MemoryProcessingResult test passed")


def test_validation_helpers():
    """Test validation helper functions."""
    print("Testing validation helpers...")
    
    # Test actor type validation
    supported_types = ["client", "synth", "synth_class", "skill_module"]
    assert validate_actor_type_supported("client", supported_types) is True
    assert validate_actor_type_supported("invalid_type", supported_types) is False
    print("✓ Actor type validation helper test passed")
    
    # Test text length validation
    assert validate_text_length("Hello world", min_length=1, max_length=100) is True
    assert validate_text_length("", min_length=1, max_length=100) is False
    assert validate_text_length("x" * 101, min_length=1, max_length=100) is False
    print("✓ Text length validation helper test passed")
    
    # Test validation error creation
    error = create_validation_error("text_content", "cannot be empty", "")
    assert error.error_code == "VALIDATION_ERROR"
    assert "Validation failed for text_content" in error.error_message
    print("✓ Validation error creation test passed")


if __name__ == '__main__':
    print("Running MemoryMaker models tests...")
    print("=" * 50)
    
    try:
        test_memory_maker_request()
        test_validation_errors()
        test_memory_entity()
        test_processing_result()
        test_validation_helpers()
        
        print("=" * 50)
        print("✅ All models tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)