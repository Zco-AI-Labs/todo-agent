import os
import asyncio
from google.antigravity import Agent, LocalAgentConfig, CapabilitiesConfig
from google.antigravity.types import BuiltinTools

class TodoAgent:
    def __init__(self):
        # Initialize configuration with standard/empty properties.
        # Paths and workspaces will be populated dynamically at runtime.
        self.config = LocalAgentConfig(
            skills_paths=[],
            workspaces=[],
            capabilities=CapabilitiesConfig(
                disabled_tools=[
                    BuiltinTools.LIST_DIR,
                    BuiltinTools.SEARCH_DIR,
                    BuiltinTools.FIND_FILE,
                    BuiltinTools.VIEW_FILE,
                    BuiltinTools.CREATE_FILE,
                    BuiltinTools.EDIT_FILE,
                    BuiltinTools.RUN_COMMAND,
                    BuiltinTools.GENERATE_IMAGE
                ]
            ),
            vertex=True,
            project=os.getenv("PROJECT_ID") or os.getenv("GCP_PROJECT_ID") or "hubscape-geap",
            location=os.getenv("GCP_LOCATION") or os.getenv("LOCATION") or "us-central1",
            model="gemini-2.5-flash"
        )

    async def query(self, question: str) -> str:
        """
        Interface method invoked by GEAP / Vertex AI Reasoning Engines.
        """
        # Resolve path to container's local skill directory dynamically at runtime
        runtime_dir = os.path.dirname(os.path.abspath(__file__))
        self.config.skills_paths = [runtime_dir]
        self.config.workspaces = []
        
        async with Agent(config=self.config) as agent:
            response = await agent.chat(question)
            await response.resolve()
            return await response.text()

# Singleton instance used as the serialization target
todo_agent_app = TodoAgent()
