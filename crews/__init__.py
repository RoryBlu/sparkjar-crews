"""
Crew handlers registry for SparkJAR Crew System
"""

from typing import Any, Dict, Type

import logging
logger = logging.getLogger(__name__)

from .base import BaseCrewHandler
# Skip gen_crew import to avoid api.models dependency
# from .gen_crew.gen_crew_handler import GenCrewHandler
from .book_ingestion_crew import BookIngestionCrewHandler
from .memory_maker_crew import MemoryMakerCrewHandler

# Registry of available crew handlers
CREW_REGISTRY: Dict[str, Any] = {
    # "gen_crew": GenCrewHandler,  # Has api.models dependency
    "book_ingestion_crew": BookIngestionCrewHandler,
    "memory_maker_crew": MemoryMakerCrewHandler,
}

__all__ = ["CREW_REGISTRY", "BaseCrewHandler"]