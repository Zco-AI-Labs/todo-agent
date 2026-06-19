import os
import asyncio
from google.antigravity import Agent, LocalAgentConfig

class TodoAgent:
    def __init__(self):
        # Resolve path to local skill directory (containing SKILL.md and scripts/)
        self.config = LocalAgentConfig(
            skills_paths=[os.path.dirname(os.path.abspath(__file__))],
            vertex=True,
            project=os.getenv("PROJECT_ID") or os.getenv("GCP_PROJECT_ID") or "hubscape-geap",
            location=os.getenv("GCP_LOCATION") or os.getenv("LOCATION") or "us-central1"
        )

    async def query(self, question: str) -> str:
        """
        Interface method invoked by GEAP / Vertex AI Reasoning Engines.
        """
        async with Agent(config=self.config) as agent:
            response = await agent.chat(question)
            await response.resolve()
            return response.text()

# Singleton instance used as the serialization target
todo_agent_app = TodoAgent()
