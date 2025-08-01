"""Test utilities for memory_maker_crew package."""

# Provide minimal stubs for `sparkjar_shared` so unit tests can run
import sys
import types

if 'sparkjar_shared.crews' not in sys.modules:
    sparkjar_shared = types.ModuleType('sparkjar_shared')
    crews_module = types.ModuleType('sparkjar_shared.crews')

    # Import local implementations used by the code under test
    from sparkjar_shared.utils.simple_crew_logger import SimpleCrewLogger
    from sparkjar_shared.utils.crew_logger import CrewExecutionLogger

    crews_module.SimpleCrewLogger = SimpleCrewLogger
    crews_module.CrewExecutionLogger = CrewExecutionLogger

    sparkjar_shared.crews = crews_module
    sys.modules['sparkjar_shared'] = sparkjar_shared
    sys.modules['sparkjar_shared.crews'] = crews_module
