# sparkjar-crews

SparkJAR CrewAI crews extracted from monorepo for independent execution.

## Quick Start

```bash
# Create virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run a crew
python main.py memory_maker_crew --text "Process this corporate policy into memories"
python main.py entity_research_crew --entity "OpenAI" --domain "technology"
```

## Available Crews

- **memory_maker_crew**: Processes text into structured memories
- **entity_research_crew**: Researches entities and organizations
- **book_ingestion_crew**: Processes books and documents
- **contact_form**: Handles contact form submissions

## Project Structure

```
sparkjar-crews/
├── crews/              # All crew implementations
│   ├── memory_maker_crew/
│   ├── entity_research_crew/
│   ├── book_ingestion_crew/
│   └── contact_form/
├── tools/              # Shared tools for crews
├── utils/              # Utility functions
├── main.py            # Direct execution entry point
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

## Notes

- This is extracted from the sparkjar-crew monorepo
- Crews can now run independently without the API layer
- Direct execution means faster iteration and testing
- No more import issues or dependency conflicts!