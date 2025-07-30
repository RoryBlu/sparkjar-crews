"""
Crew registry for SparkJAR Crews API Service

This module maintains a registry of available crews that can be executed via the API.
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Import available crew handlers
try:
    from crews.memory_maker_crew.memory_maker_crew_handler import MemoryMakerCrewHandler
except ImportError as e:
    logger.warning(f"Failed to import MemoryMakerCrewHandler: {e}")
    MemoryMakerCrewHandler = None

try:
    from crews.entity_research_crew.entity_research_crew_handler import EntityResearchCrewHandler
except ImportError as e:
    logger.warning(f"Failed to import EntityResearchCrewHandler: {e}")
    EntityResearchCrewHandler = None

try:
    from crews.book_ingestion_crew.book_ingestion_crew_handler import BookIngestionCrewHandler
except ImportError as e:
    logger.warning(f"Failed to import BookIngestionCrewHandler: {e}")
    BookIngestionCrewHandler = None

try:
    from crews.book_translation_crew.book_translation_crew_handler import BookTranslationCrewHandler
except ImportError as e:
    logger.warning(f"Failed to import BookTranslationCrewHandler: {e}")
    BookTranslationCrewHandler = None

# Registry of available crew handlers
CREW_REGISTRY: Dict[str, Any] = {}

# Add crews to registry if they were successfully imported
if MemoryMakerCrewHandler:
    CREW_REGISTRY["memory_maker_crew"] = MemoryMakerCrewHandler

if EntityResearchCrewHandler:
    CREW_REGISTRY["entity_research_crew"] = EntityResearchCrewHandler

if BookIngestionCrewHandler:
    CREW_REGISTRY["book_ingestion_crew"] = BookIngestionCrewHandler

if BookTranslationCrewHandler:
    CREW_REGISTRY["book_translation_crew"] = BookTranslationCrewHandler

logger.info(f"Loaded {len(CREW_REGISTRY)} crews: {list(CREW_REGISTRY.keys())}")

__all__ = ["CREW_REGISTRY"]