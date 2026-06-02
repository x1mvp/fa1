from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from typing import List
import yaml
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@CrewBase
class OpenAgentFactory():
    """Main multi-agent factory crew"""
    
    def __init__(self):
        self.agents_config = {}
        self.load_agent_configs()
        
    def load_agent_configs(self):
        """Load agent configurations from YAML files"""
        import glob
        agent_files = glob.glob('/app/agents/*.yaml')
        
        for filepath in agent_files:
            try:
                with open(filepath, 'r') as f:
                    config = yaml.safe_load(f)
                    self.agents_config.update(config)
            except Exception as e:
                print(f"Warning: Could not load {filepath}: {e}")

    @agent
    def researcher(self) -> Agent:
        config = self.agents_config.get('researcher', {})
        model = os.getenv('OLLAMA_MODEL', 'llama3.1:8b')
        
        return Agent(
            role=config.get('role', 'Researcher'),
            goal=config.get('goal', 'Find information'),
            backstory=config.get('backstory', ''),
            verbose=config.get('verbose', True),
            max_iter=config.get('max_iter', 5),
            memory=config.get('memory', True),
            allow_delegation=config.get('allow_delegation', False),
            llm=LLM(
                model=f"ollama/{model}",
                base_url=os.getenv('OLLAMA_BASE_URL', 'http://ollama:11434')
            )
        )

    @agent
    def coder(self) -> Agent:
        config = self.agents_config.get('coder', {})
        model = os.getenv('OLLAMA_MODEL', 'mistral:7b')
        
        return Agent(
            role=config.get('role', 'Developer'),
            goal=config.get('goal', 'Write code'),
            backstory=config.get('backstory', ''),
            verbose=config.get('verbose', True),
            max_iter=config.get('max_iter', 3),
            memory=config.get('memory', True),
            allow_delegation=config.get('allow_delegation', False),
            llm=LLM(
                model=f"ollama/{model}",
                base_url=os.getenv('OLLAMA_BASE_URL', 'http://ollama:11434')
            )
        )

    @agent
    def reviewer(self) -> Agent:
        config = self.agents_config.get('reviewer', {})
        model = os.getenv('OLLAMA_MODEL', 'llama3.1:8b')
        
        return Agent(
            role=config.get('role', 'Reviewer'),
            goal=config.get('goal', 'Review outputs'),
            backstory=config.get('backstory', ''),
            verbose=config.get('verbose', True),
            max_iter=config.get('max_iter', 2),
            memory=config.get('memory', False),
            allow_delegation=config.get('allow_delegation', False),
            llm=LLM(
                model=f"ollama/{model}",
                base_url=os.getenv('OLLAMA_BASE_URL', 'http://ollama:11434')
            )
        )

    @task
    def research_task(self) -> Task:
        return Task(
            description="Research the topic: {topic}. Find accurate information and cite sources.",
            expected_output="Comprehensive research report with findings and sources",
            agent=self.researcher
        )

    @task
    def code_task(self) -> Task:
        return Task(
            description="Write Python code for: {topic}. Include error handling and examples.",
            expected_output="Working Python code with documentation and error handling",
            agent=self.coder
        )

    @task
    def review_task(self) -> Task:
        return Task(
            description="Review the previous outputs for quality, security, and completeness.",
            expected_output="Detailed review with recommendations for improvement",
            agent=self.reviewer
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[self.researcher, self.coder, self.reviewer],
            tasks=[self.research_task, self.code_task, self.review_task],
            process=Process.sequential,
            verbose=True,
            memory=True
        )
