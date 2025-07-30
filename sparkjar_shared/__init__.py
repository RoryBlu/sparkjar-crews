"""Minimal stub of sparkjar_shared used for tests."""

from types import SimpleNamespace
from .crews import BaseCrewHandler, SimpleCrewLogger, CrewExecutionLogger

crews = SimpleNamespace(
    BaseCrewHandler=BaseCrewHandler,
    SimpleCrewLogger=SimpleCrewLogger,
    CrewExecutionLogger=CrewExecutionLogger,
)

__all__ = ["crews"]
