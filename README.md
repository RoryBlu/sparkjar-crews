# sparkjar-crews

SparkJAR CrewAI crews microservice - production-ready AI agent orchestration.

## Introduction

This repository contains the CrewAI-based agent crews that power SparkJAR's AI capabilities. Originally part of a monorepo, these crews have been extracted for independent deployment and development. The system follows CrewAI standards with YAML-based configuration and includes comprehensive tooling for memory management, document processing, and research tasks.

## Quick Start

```bash
# Create virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# Install dependencies including sparkjar-shared
pip install -r requirements.txt
pip install -e ../sparkjar-shared  # Required for database models

# Run a crew
python main.py memory_maker_crew --text "Process this corporate policy into memories"
python main.py entity_research_crew --entity "OpenAI" --domain "technology"
```

## Available Crews

### Production-Ready Crews
- **memory_maker_crew**: Processes text into structured memories with hierarchical access
- **entity_research_crew**: Researches entities and organizations with web search capabilities

### Crews Under Development
- **book_ingestion_crew**: OCR processing for handwritten manuscripts (recently fixed for Google Drive hanging)
- **contact_form**: Handles contact form submissions with automated responses

## Project Structure

```
sparkjar-crews/
├── .kiro/              # Specification documents using KIRO methodology
│   └── specs/          # Crew requirements and design documents
├── crews/              # All crew implementations
│   ├── memory_maker_crew/
│   │   ├── config/    # YAML configurations (agents.yaml, tasks.yaml)
│   │   ├── crew.py    # Crew implementation
│   │   └── main.py    # Direct execution entry
│   ├── entity_research_crew/
│   ├── book_ingestion_crew/
│   └── contact_form/
├── tools/              # Shared tools for crews
│   ├── sj_memory_tool.py          # Memory storage and retrieval
│   ├── sj_sequential_thinking.py  # Agent reasoning tool
│   ├── google_drive_tool.py       # Google Drive integration
│   └── image_viewer_tool.py       # OCR with GPT-4o
├── utils/              # Utility functions
├── main.py            # Direct execution entry point
├── crew_registry.py   # Crew registration system
└── requirements.txt   # Python dependencies
```

## Running Crews

### Option 1: Command Line
```bash
python main.py memory_maker_crew --text "Your text here"
```

### Option 2: Config File
```bash
python main.py memory_maker_crew --config config.json
```

### Option 3: Import and Use
```python
from crews.memory_maker_crew.crew import MemoryMakerCrew

crew = MemoryMakerCrew()
result = crew.kickoff(inputs={
    "text_content": "Your text here",
    "actor_type": "human",
    "actor_id": "user-123"
})
```

## Environment Variables

Create a `.env` file with:
```
OPENAI_API_KEY=your-key-here
GOOGLE_API_KEY=your-key-here  # Optional, for search tools
```

## Recent Updates

### July 2025
- Fixed book ingestion crew hanging issue with Google Drive downloads
- Consolidated multiple crew versions (removed v2, v3, v4 duplicates) 
- Restored YAML-based configuration following CrewAI standards
- Added comprehensive .kiro specifications for all crews
- Fixed database column naming issues (ClientUsers.clients_id)

## Development Standards

### CrewAI Configuration
All crews must follow CrewAI standards:
- YAML-based agent and task definitions in `config/` directory
- Use standard OpenAI models (gpt-4o-mini, gpt-4o) 
- Implement crews using `kickoff()` or `kickoff_for_each()` methods
- No hardcoded agents or tasks in Python files

### KISS Principle
Following CLAUDE.md guidelines:
- Keep implementations simple and straightforward
- No unnecessary complexity or feature creep
- Test with real data before declaring production-ready
- One version only - no v2, v3, v4 files

### Documentation Requirements
- Each crew must have a README.md explaining its purpose
- Use .kiro methodology for specifications (see .kiro/specs/)
- Document all tool dependencies and configurations
- Include example usage and test commands

## Troubleshooting

### Common Issues
1. **Import Errors**: Ensure sparkjar-shared is installed: `pip install -e ../sparkjar-shared`
2. **Model Not Found**: Use standard models like gpt-4o-mini, not gpt-4.1 series
3. **Database Errors**: Check DATABASE_URL_DIRECT environment variable
4. **Google Drive Access**: Ensure service account credentials are properly configured

### Getting Help
- Check .kiro/specs/ for detailed crew specifications
- Review CLAUDE.md for development principles
- See individual crew README files for specific guidance