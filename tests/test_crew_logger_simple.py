import logging

import pytest

from sparkjar_shared.database import EVENTS
from utils.crew_logger import CrewExecutionLogger


@pytest.mark.asyncio
async def test_logger_persists_events():
    EVENTS.clear()
    logger = CrewExecutionLogger("job-test")
    async with logger.capture_crew_logs():
        logging.getLogger("crewai").info("test message")
    event_types = [e.event_type for e in EVENTS]
    assert "crew_execution_start" in event_types
    assert "crew_execution_logs" in event_types
    assert "crew_execution_end" in event_types
    assert any("test message" in str(e.event_data) for e in EVENTS)
