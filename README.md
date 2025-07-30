# sparkjar-crews

SparkJAR CrewAI crews microservice - production-ready AI agent orchestration.

## Introduction

This repository contains the CrewAI-based agent crews that power SparkJAR's AI capabilities. The crews are exposed via an HTTP API service that integrates with the main SparkJAR platform. The system follows CrewAI standards with YAML-based configuration and includes comprehensive tooling for memory management, document processing, and research tasks.

## Architecture

This service provides HTTP endpoints for crew execution, replacing the previous direct import model:
- **HTTP API**: FastAPI server on port 8001 for remote crew execution
- **Authentication**: JWT-based with `sparkjar_internal` scope requirement
- **Crew Handlers**: All crews extend `BaseCrewHandler` from sparkjar-shared
- **Async Execution**: Full async/await support for scalability

## Quick Start

### Running the HTTP API Server

```bash
# Create virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# Install dependencies including sparkjar-shared
pip install -e ../sparkjar-shared  # Install shared package first
pip install -r requirements.txt

# Start the API server
uvicorn api.server:app --reload --host 0.0.0.0 --port 8001
```

### Direct Crew Execution (Development Only)

```bash
# For development/testing only
python main.py memory_maker_crew --text "Process this corporate policy into memories"
python main.py entity_research_crew --entity "OpenAI" --domain "technology"
```

## Available Crews

### Production-Ready Crews
- **memory_maker_crew**: Processes text into structured memories with hierarchical access
- **entity_research_crew**: Researches entities and organizations with web search capabilities
- **book_ingestion_crew**: OCR processing for handwritten manuscripts with GPT-4o vision
- **book_translation_crew**: Translates ingested books using GPT-4.1 models

### Crews Under Development
- **contact_form**: Handles contact form submissions with automated responses
- **blog_writer_hierarchical**: Hierarchical blog content generation crew

## Project Structure

```
sparkjar-crews/
├── api/                # HTTP API implementation
│   ├── server.py       # FastAPI application
│   ├── crew_registry.py # Crew registration and discovery
│   └── logging_config.py # Structured logging setup
├── crews/              # All crew implementations
│   ├── memory_maker_crew/
│   │   ├── config/    # YAML configurations (agents.yaml, tasks.yaml)
│   │   ├── crew.py    # Crew implementation
│   │   ├── main.py    # Direct execution entry
│   │   └── memory_maker_crew_handler.py  # HTTP handler
│   ├── entity_research_crew/
│   ├── book_ingestion_crew/
│   └── book_translation_crew/
├── tools/              # Shared tools for crews
│   ├── sj_memory_tool.py          # Memory storage and retrieval
│   ├── sj_sequential_thinking.py  # Agent reasoning tool
│   ├── google_drive_tool.py       # Google Drive integration
│   └── image_viewer_tool.py       # OCR with GPT-4o
├── utils/              # Utility functions
├── main.py            # Direct execution entry point
└── requirements.txt   # Python dependencies
```

## API Endpoints

### Execute Crew
```bash
POST /execute_crew
Authorization: Bearer <JWT_TOKEN>

{
    "crew_name": "memory_maker_crew",
    "inputs": {
        "text_content": "Your text here",
        "actor_type": "human",
        "actor_id": "user-123"
    }
}
```

### Health Check
```bash
GET /health
```

### List Available Crews
```bash
GET /crews
Authorization: Bearer <JWT_TOKEN>
```

## Development Usage

### Option 1: Direct Command Line (Dev Only)
```bash
python main.py memory_maker_crew --text "Your text here"
```

### Option 2: Import Handler
```python
from crews.memory_maker_crew.memory_maker_crew_handler import MemoryMakerCrewHandler

handler = MemoryMakerCrewHandler()
result = await handler.execute({
    "text_content": "Your text here",
    "actor_type": "human",
    "actor_id": "user-123"
})
```

## Environment Variables

Create a `.env` file with:
```
# Required
OPENAI_API_KEY=your-key-here
API_SECRET_KEY=your-secret-key  # For JWT verification
DATABASE_URL=postgresql://...   # PostgreSQL connection

# Optional
GOOGLE_API_KEY=your-key-here    # For search tools
CHROMA_URL=http://chroma:8000   # ChromaDB for vector storage
MEMORY_SERVICE_URL=http://memory-internal:8001

# Service Configuration
API_HOST=0.0.0.0
API_PORT=8001
ENVIRONMENT=development
# Additional Optional Variables
DATABASE_URL_DIRECT=postgresql://...   # Direct DB connection for tools
SERPER_API_KEY=your-key-here          # Serper search API
SCRAPER_SESSION_TTL=300               # Seconds to keep headless scraper alive
REDIS_URL=redis://localhost:6379/0    # Redis cache for scraper sessions
EMBEDDING_PROVIDER=openai             # Embedding provider (custom or openai)
OPENAI_EMBEDDING_MODEL=text-embedding-3-small  # Embedding model for OpenAI
OPENAI_EMBEDDING_DIMENSION=1536       # Embedding dimension for OpenAI
OPENAI_API_URL=https://api.openai.com/v1/embeddings  # Override embeddings endpoint
EMBEDDING_DIMENSION=768               # Dimension for custom embedding service
GOOGLE_CSE_ID=your-cse-id             # Google Custom Search ID
GOOGLE_SEARCH_API_URL=https://www.googleapis.com/customsearch/v1  # Custom search endpoint
MEMORY_MAKER_TIMEOUT=30               # Timeout for memory maker crew
MEMORY_MAKER_RETRY_ATTEMPTS=3         # Retry attempts for memory maker crew
MEMORY_MAKER_RETRY_BACKOFF=2.0        # Exponential backoff for memory maker
MEMORY_MAKER_MAX_TEXT_LENGTH=100000   # Max text length for memory maker
MEMORY_MAKER_DEBUG=false              # Debug logging for memory maker
VERVELYN_PAYLOAD_PATH=/path/to/payload # Path for dev Vervelyn payload
VERBOSE=false                         # Extra debug output
```

## Recent Updates

### July 2025 - Architecture Cleanup
- **NEW**: HTTP API service for remote crew execution
- **NEW**: All crews now extend BaseCrewHandler from sparkjar-shared
- **NEW**: JWT authentication with sparkjar_internal scope
- **NEW**: Comprehensive handler pattern for all crews
- Fixed book ingestion crew hanging issue with Google Drive downloads
- Consolidated multiple crew versions (removed v2, v3, v4 duplicates)
- Restored YAML-based configuration following CrewAI standards
- Added comprehensive .kiro specifications for all crews
- Fixed database column naming issues (ClientUsers.clients_id)

## Deployment

This service is designed to run on Railway as a microservice:

```bash
# Railway deployment
railway up

# Or Docker
docker build -t sparkjar-crews .
docker run -p 8001:8001 --env-file .env sparkjar-crews
```

## Integration with SparkJAR Platform

The sparkjar-crew-api service communicates with this crews service via HTTP:

1. API Gateway receives crew execution request
2. Checks feature flags for remote execution
3. Forwards request to this service via HTTP + JWT
4. Returns results to client

Enable remote execution in API service:
```bash
export FEATURE_FLAG_USE_REMOTE_CREWS_MEMORY_MAKER_CREW=true
```

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