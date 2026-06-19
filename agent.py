import os
import asyncio
from google.antigravity import Agent, LocalAgentConfig

class TodoAgent:
    def __init__(self):
        # Resolve path to local skill directory (containing SKILL.md and scripts/)
        self.config = LocalAgentConfig(
            skills_paths=[os.path.dirname(os.path.abspath(__file__))]
        )

    def query(self, question: str) -> str:
        """
        Interface method invoked by GEAP / Vertex AI Reasoning Engines.
        """
        async def _run():
            async with Agent(config=self.config) as agent:
                response = await agent.chat(question)
                await response.resolve()
                return response.text()
        
        return asyncio.run(_run())

# Singleton instance used as the serialization target
todo_agent_app = TodoAgent()
