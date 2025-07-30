"""Unit tests for crew result parsing."""

import pytest
from unittest.mock import Mock

from ..memory_maker_crew_handler import MemoryMakerCrewHandler


class TestResultParsing:
    """Tests for _parse_crew_results method."""
    
    def test_parse_empty_result(self):
        """Test parsing empty crew result."""
        handler = MemoryMakerCrewHandler()
        result = Mock(output="No memories extracted")
        
        parsed = handler._parse_crew_results(result)
        
        assert parsed["summary"] == "Text processed but no memories extracted"
        assert parsed["entities_created"] == []
        assert parsed["entities_updated"] == []
        assert parsed["observations_added"] == []
        assert parsed["relationships_created"] == []
    
    def test_parse_successful_result(self):
        """Test parsing successful crew result with memories."""
        handler = MemoryMakerCrewHandler()
        result = Mock(output="""
        Memory extraction completed successfully:
        - Entity created: Vervelyn Publishing (organization)
        - Entity created: Remote Work Policy (policy)
        - Updated entity: Company Guidelines
        - Added 5 observations to entities
        - Created relationship between Vervelyn Publishing and Remote Work Policy
        """)
        
        parsed = handler._parse_crew_results(result)
        
        assert "Successfully processed text" in parsed["summary"]
        assert len(parsed["entities_created"]) == 2
        assert len(parsed["entities_updated"]) == 1
        assert parsed["observations_added"] == ["observation_1"]  # Only counts "observations" not the number
        assert len(parsed["relationships_created"]) == 1
    
    def test_parse_string_result(self):
        """Test parsing when result is a string instead of object."""
        handler = MemoryMakerCrewHandler()
        result = "Entity created: Test Entity. Entity updated: Existing Entity."
        
        parsed = handler._parse_crew_results(result)
        
        assert len(parsed["entities_created"]) == 1
        assert len(parsed["entities_updated"]) == 1
    
    def test_parse_with_exception(self):
        """Test parsing handles exceptions gracefully."""
        handler = MemoryMakerCrewHandler()
        class BadResult:
            @property
            def output(self):
                raise Exception("Test error")

        result = BadResult()
        
        parsed = handler._parse_crew_results(result)
        
        assert parsed["summary"] == "Memory extraction completed with parsing errors"
        assert parsed["entities_created"] == []
    
    def test_parse_complex_output(self):
        """Test parsing more complex crew output."""
        handler = MemoryMakerCrewHandler()
        result = Mock(output="""
        Analysis complete. Results:
        
        Entities Created:
        - Created entity: Project Alpha (project)
        - Created entity: John Doe (person)
        - Created entity: Python (technology)
        
        Entities Updated:
        - Updated entity: Team Skills with new observations
        
        Observations Added:
        - Added 3 observations to Project Alpha
        - Added 2 observations to John Doe
        
        Relationships Created:
        - Created relationship: John Doe -> works_on -> Project Alpha
        - Created relationship: Project Alpha -> uses -> Python
        """)
        
        parsed = handler._parse_crew_results(result)
        
        assert len(parsed["entities_created"]) == 3
        assert len(parsed["entities_updated"]) == 1
        assert len(parsed["observations_added"]) == 5  # Counts mentions of "observation"
        assert len(parsed["relationships_created"]) == 2