"""Test configuration for memory_maker_crew package."""

import sys
import types
import pytest

# Ensure sparkjar_shared is available during test collection
if "sparkjar_shared.crews" not in sys.modules:
    sparkjar_shared = types.ModuleType("sparkjar_shared")
    crews_mod = types.ModuleType("sparkjar_shared.crews")
    from sparkjar_shared.utils.simple_crew_logger import SimpleCrewLogger
    from sparkjar_shared.utils.crew_logger import CrewExecutionLogger
    crews_mod.SimpleCrewLogger = SimpleCrewLogger
    crews_mod.CrewExecutionLogger = CrewExecutionLogger
    sparkjar_shared.crews = crews_mod
    sys.modules["sparkjar_shared"] = sparkjar_shared
    sys.modules["sparkjar_shared.crews"] = crews_mod


@pytest.fixture(scope="session", autouse=True)
def stub_sparkjar_shared():
    """Session fixture to keep stub modules loaded."""
    yield
