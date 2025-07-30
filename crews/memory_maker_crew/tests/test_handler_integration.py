"""Integration tests for MemoryMakerCrewHandler using mocks."""

import asyncio
from unittest.mock import MagicMock, patch
from uuid import uuid4

from ..memory_maker_crew_handler import MemoryMakerCrewHandler


class TestHandlerIntegration:
    """Verify handler execution with mocked crew."""

    def test_execute_successful_flow(self):
        handler = MemoryMakerCrewHandler()
        request = {
            "client_user_id": str(uuid4()),
            "actor_type": "client",
            "actor_id": str(uuid4()),
            "text_content": "Entity created: Foo. Entity updated: Bar. Observation."
        }

        fake_result = MagicMock()
        fake_result.output = request["text_content"]

        with patch(
            "crews.memory_maker_crew.memory_maker_crew_handler.MemoryMakerCrew"
        ) as MockCrew:
            crew_instance = MockCrew.return_value
            crew_instance.crew.return_value.kickoff.return_value = fake_result

            result = asyncio.run(handler.execute(request))

            crew_instance.crew.return_value.kickoff.assert_called_once()
            assert result["status"] == "completed"
            assert len(result["entities_created"]) == 1
            assert len(result["entities_updated"]) == 1
            assert result["observations_added"] == ["observation_1"]
