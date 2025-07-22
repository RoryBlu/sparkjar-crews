"""
Memory Maker Crew - Analyzes conversations and extracts structured memories.
"""

import os
from typing import List, Dict, Any
from uuid import UUID

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from tools.sj_memory_tool_hierarchical import SJMemoryToolHierarchical


@CrewBase
class MemoryMakerCrew:
    """Memory Maker Crew for conversation analysis and memory extraction."""
    
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'
    
    def __init__(self, client_user_id: str = None, actor_type: str = None, actor_id: str = None):
        """
        Initialize the Memory Maker Crew.
        
        Args:
            client_user_id: Client user identifier (optional, can be set from inputs)
            actor_type: Type of actor (synth, human, etc.) (optional, can be set from inputs)
            actor_id: Actor identifier (optional, can be set from inputs)
        """
        self.client_user_id = client_user_id
        self.actor_type = actor_type
        self.actor_id = actor_id
        
        # Initialize memory tool with hierarchical support
        self.memory_tool = SJMemoryToolHierarchical()
        
        # Set the actor context if provided
        if all([actor_type, actor_id, client_user_id]):
            self.memory_tool.set_actor_context(
                actor_type=actor_type,
                actor_id=actor_id,
                client_id=client_user_id
            )
        
    @agent
    def text_analyzer(self) -> Agent:
        """
        Agent that analyzes text content to identify entities, 
        relationships, and key information.
        """
        return Agent(
            config=self.agents_config['text_analyzer'],
            tools=[self.memory_tool],
            verbose=True
        )
        
    @agent
    def memory_structurer(self) -> Agent:
        """
        Agent that structures identified information into proper
        memory entities and observations.
        """
        return Agent(
            config=self.agents_config['memory_structurer'],
            tools=[self.memory_tool],
            verbose=True
        )
        
    @task
    def analyze_text_task(self) -> Task:
        """
        Task to analyze the text and extract key information.
        """
        return Task(
            config=self.tasks_config['analyze_text'],
            agent=self.text_analyzer()
        )
        
    @task
    def structure_memories_task(self) -> Task:
        """
        Task to structure extracted information into memory entities.
        """
        return Task(
            config=self.tasks_config['structure_memories'],
            agent=self.memory_structurer()
        )
        
    @task
    def store_memories_task(self) -> Task:
        """
        Task to store structured memories using the memory tool.
        """
        return Task(
            config=self.tasks_config['store_memories'],
            agent=self.memory_structurer()
        )
        
    @crew
    def crew(self) -> Crew:
        """Creates the Memory Maker Crew."""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=2
        )
        
    def kickoff(self, inputs: Dict[str, Any]) -> Any:
        """
        Run the crew with provided inputs.
        
        Args:
            inputs: Dictionary containing:
                - text_content: The text to analyze
                - actor_type: Type of actor (client, synth, human, etc.)
                - actor_id: Actor identifier
                - client_user_id: Client user identifier
        """
        # Extract actor context from inputs
        actor_type = inputs.get('actor_type', self.actor_type)
        actor_id = inputs.get('actor_id', self.actor_id)
        client_user_id = inputs.get('client_user_id', self.client_user_id)
        
        # Set actor context in memory tool
        if all([actor_type, actor_id, client_user_id]):
            self.memory_tool.set_actor_context(
                actor_type=actor_type,
                actor_id=actor_id,
                client_id=client_user_id
            )
        
        # Run the crew
        return self.crew().kickoff(inputs=inputs)