# Codex Guidelines for Making a Crew

This guide outlines the standard patterns and best practices for implementing new crews in the `sparkjar-crews` repository. It consolidates details from the existing codebase, internal documentation, and current research on LLM prompting strategies such as Chain of Draft (CoD) and Chain of Thought (CoT).

## 1. Architecture Overview

A crew consists of:

1. **YAML configuration** for agents and tasks stored under a crew's `config/` directory.
2. **Crew implementation** using the `CrewBase` decorator from CrewAI (`crew.py`).
3. **Handler class** extending `BaseCrewHandler` to validate requests and run the crew (`*_crew_handler.py`).
4. **Registration** of the handler in `crew_registry.py` so the API service can discover the crew.

The repository structure described in the main `README.md` illustrates this pattern:

```
sparkjar-crews/
├── api/                # FastAPI server
├── crews/              # Individual crews
│   ├── memory_maker_crew/
│   │   ├── config/    # YAML configuration
│   │   ├── crew.py    # Crew implementation
│   │   └── memory_maker_crew_handler.py
│   └── ...            # Other crews
├── tools/              # Shared tools
└── utils/              # Helper utilities
```

Crew implementations rely on the `kickoff()` method to run sequential tasks defined in YAML. Base handlers provide input validation and logging via `SimpleCrewLogger` or `EnhancedCrewLogger`.

## 2. Development Standards

The repository enforces several conventions (see `README.md` lines 207–227):

- Keep agent and task definitions in YAML; avoid hardcoded values in Python.
- Use standard OpenAI models such as `gpt-4o-mini` and `gpt-4o`.
- Follow the KISS principle—one version of each crew with minimal complexity.
- Document each crew with a `README.md` and maintain specifications under `.kiro/specs/`.

## 3. Recommended Workflow

1. **Design the crew**
   - Draft requirements using the KIRO format (introduction, numbered requirements, user stories, and EARS acceptance criteria).
   - Define agents in `agents.yaml` with clear goals, backstories, and LLM parameters.
   - Define tasks in `tasks.yaml`, referencing agent names and specifying expected outputs.
2. **Implement crew.py**
   - Use the `@CrewBase` class decorator to map YAML configs.
   - Provide agent factory methods with the `@agent` decorator.
   - Provide task factory methods with the `@task` decorator.
   - Assemble the crew with the `@crew` method, typically using `Process.sequential`.
   - Implement a `kickoff(inputs: dict)` function (or `kickoff_for_each`) that sets any context and calls `self.crew().kickoff(inputs=inputs)`.
3. **Create a handler**
   - Subclass `BaseCrewHandler` and implement `async def execute(self, request_data)`.
   - Validate required fields and transform results into a serializable format.
   - Log execution start, completion, and errors through the base logger utilities.
4. **Register the handler**
   - Add the handler to `CREW_REGISTRY` in `crew_registry.py` so the API can list and execute the crew.

## 4. Prompting Strategies

Recent research introduced **Chain of Draft (CoD)**, a strategy for efficient reasoning. CoD encourages models to produce concise intermediate drafts rather than verbose step‑by‑step explanations. According to the paper *Chain of Draft: Thinking Faster by Writing Less* (Xu et al., 2025), CoD achieves accuracy comparable to Chain of Thought while using as little as 7.6% of the tokens. CoD reduces latency and cost without sacrificing quality.

When designing new crews:

- Use CoD-style prompts when short intermediate reasoning is sufficient.
- Retain CoT-style detailed reasoning for tasks that benefit from full transparency or where step validation is required.
- Avoid unnecessary retries or excessive loops. Instead, design tasks so that each agent has enough context to succeed in one or two attempts.

## 5. Data Flow and Memory

Crews rely on tools for memory and sequential thinking. To ensure that data flows cleanly between tasks:

- Pass structured context objects rather than free‑form text when calling tools.
- Use the provided memory tools (e.g., `SJMemoryToolHierarchical`) to set actor context and store observations.
- Capture intermediate outputs and reuse them in later tasks rather than rerunning previous steps.
- Keep sequential reasoning concise—favor CoD over lengthy CoT when possible to minimize token usage.

## 6. Error Handling and Retries

The Book Ingestion Crew’s README stresses sequential processing and limited LLM calls. Excessive retries often yield minimal gains. Guidelines:

- Validate inputs early and provide clear error messages.
- Limit retry attempts to a sensible default (e.g., 3) with exponential backoff.
- Log failures with enough context for debugging but avoid leaking sensitive data.
- If an agent consistently fails, review prompts and ensure required tools are available rather than increasing the retry count.

## 7. Example Skeleton

Below is a minimal skeleton for a new crew (excluding full YAML for brevity):

```python
# crews/my_new_crew/crew.py
from crewai import Agent, Crew, Process, Task, CrewBase, agent, task, crew

@CrewBase
class MyNewCrew:
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def worker(self) -> Agent:
        return Agent(config=self.agents_config['worker'])

    @task
    def do_work(self) -> Task:
        return Task(config=self.tasks_config['do_work'], agent=self.worker())

    @crew
    def crew(self) -> Crew:
        return Crew(agents=self.agents, tasks=self.tasks, process=Process.sequential, verbose=True)

    def kickoff(self, inputs: dict):
        return self.crew().kickoff(inputs=inputs)
```

```python
# crews/my_new_crew/my_new_crew_handler.py
from crews.base import BaseCrewHandler
from .crew import MyNewCrew

class MyNewCrewHandler(BaseCrewHandler):
    async def execute(self, request_data: dict) -> dict:
        self.log_execution_start(request_data)
        crew = MyNewCrew()
        result = crew.kickoff(request_data)
        self.log_execution_complete(result)
        return {
            "status": "completed",
            "result": result,
        }
```

Register the handler:

```python
# crew_registry.py
CREW_REGISTRY = {
    "my_new_crew": MyNewCrewHandler,
    # existing crews...
}
```

## 8. Testing and Documentation

- Provide unit tests for any new tools and handler logic.
- Include integration tests if the crew interacts with external services.
- Document example requests and expected outputs in the crew’s README.
- Keep docs up to date with configuration options and environment variables.

## 9. Key Takeaways

1. Keep crews simple and maintainable—follow the existing directory structure and YAML‑driven configuration.
2. Prefer concise reasoning (CoD) to verbose CoT when it maintains accuracy.
3. Validate data and limit retries to avoid wasted API calls.
4. Use shared tools and memory utilities for consistent behavior across crews.
5. Document everything—README files, KIRO specs, and example usage.

Following these guidelines will ensure new crews integrate smoothly with the SparkJAR platform while delivering accurate, efficient results.
