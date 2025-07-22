#!/usr/bin/env python
"""
SparkJAR Crews - Direct Execution Entry Point

This allows running crews directly without the API layer.
Example:
    python main.py memory_maker_crew --text "Process this text into memories"
    python main.py entity_research_crew --entity "OpenAI" --domain "technology"
"""
import argparse
import json
import sys
from pathlib import Path

# Import available crews
from crews.memory_maker_crew.crew import MemoryMakerCrew
from crews.entity_research_crew.crew import EntityResearchCrew
from crews.book_ingestion_crew.crew import BookIngestionCrew
from crews.contact_form.crew import ContactFormCrew

# Crew mapping
AVAILABLE_CREWS = {
    "memory_maker_crew": MemoryMakerCrew,
    "entity_research_crew": EntityResearchCrew,
    "book_ingestion_crew": BookIngestionCrew,
    "contact_form": ContactFormCrew,
}

def main():
    parser = argparse.ArgumentParser(
        description="Run SparkJAR Crews directly",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("crew", choices=list(AVAILABLE_CREWS.keys()),
                       help="The crew to run")
    parser.add_argument("--config", type=str,
                       help="Path to JSON config file")
    parser.add_argument("--text", type=str,
                       help="Text input for memory_maker_crew")
    parser.add_argument("--entity", type=str,
                       help="Entity name for entity_research_crew")
    parser.add_argument("--domain", type=str, default="general",
                       help="Domain for entity_research_crew")
    parser.add_argument("--output", type=str,
                       help="Save output to file")
    
    args = parser.parse_args()
    
    # Build inputs based on crew type
    inputs = {}
    
    if args.config:
        with open(args.config, 'r') as f:
            inputs = json.load(f)
    else:
        # Build inputs from command line args
        if args.crew == "memory_maker_crew" and args.text:
            inputs = {
                "text_content": args.text,
                "actor_type": "human",
                "actor_id": "test-user",
                "client_user_id": "test-client"
            }
        elif args.crew == "entity_research_crew" and args.entity:
            inputs = {
                "entity_name": args.entity,
                "entity_domain": args.domain
            }
        else:
            print(f"Error: Missing required arguments for {args.crew}")
            parser.print_help()
            sys.exit(1)
    
    # Run the crew
    print(f"🚀 Running {args.crew}...")
    crew_class = AVAILABLE_CREWS[args.crew]
    crew = crew_class()
    
    result = crew.kickoff(inputs=inputs)
    
    # Display results
    print("\n✅ Crew execution completed!")
    print("-" * 50)
    print(result)
    
    # Save if requested
    if args.output:
        output_data = {
            "crew": args.crew,
            "inputs": inputs,
            "result": str(result)
        }
        with open(args.output, 'w') as f:
            json.dump(output_data, f, indent=2)
        print(f"\n💾 Results saved to {args.output}")

if __name__ == "__main__":
    main()