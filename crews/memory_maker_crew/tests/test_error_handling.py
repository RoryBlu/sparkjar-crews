"""Unit tests for error handling in MemoryMakerCrewHandler."""

import asyncio
from uuid import uuid4

from ..memory_maker_crew_handler import MemoryMakerCrewHandler


class TestErrorHandling:
    """Tests for error scenarios in the handler."""

    def test_missing_required_fields(self):
        handler = MemoryMakerCrewHandler()
        result = asyncio.run(handler.execute({"actor_type": "client"}))
        assert result["status"] == "failed"
        assert "Missing required fields" in result["error"]

    def test_invalid_text_content(self):
        handler = MemoryMakerCrewHandler()
        request = {
            "client_user_id": str(uuid4()),
            "actor_type": "client",
            "actor_id": str(uuid4()),
            "text_content": "   "
        }
        result = asyncio.run(handler.execute(request))
        assert result["status"] == "failed"
        assert result["error"] == "text_content must be a non-empty string"
