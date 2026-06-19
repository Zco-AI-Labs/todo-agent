import os
import asyncio
import importlib.util
import re
from google.antigravity import Agent, LocalAgentConfig, CapabilitiesConfig
from google.antigravity.types import BuiltinTools, CustomSystemInstructions
from google.antigravity.hooks import policy

def load_local_tools(scripts_dir: str) -> list:
    tools = []
    if not os.path.exists(scripts_dir):
        return tools
    for filename in os.listdir(scripts_dir):
        if filename.endswith(".py") and not filename.startswith("_"):
            module_name = filename[:-3]
            file_path = os.path.join(scripts_dir, filename)
            try:
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    func = getattr(module, module_name, None)
                    if func and callable(func):
                        tools.append(func)
            except Exception:
                pass
    return tools

class TodoAgent:
    def __init__(self):
        # Initialize configuration with empty properties.
        # We will load paths, tools, and system prompt dynamically at runtime.
        self.config = LocalAgentConfig(
            skills_paths=[],
            workspaces=[],
            tools=[],
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
            policies=[policy.allow_all()],
            vertex=True,
            project=os.getenv("PROJECT_ID") or os.getenv("GCP_PROJECT_ID") or "hubscape-geap",
            location=os.getenv("GCP_LOCATION") or os.getenv("LOCATION") or "us-central1",
            model="gemini-2.5-flash"
        )

    async def query(self, question: str, context: dict = None) -> str:
        """
        Interface method invoked by GEAP / Vertex AI Reasoning Engines.
        """
        runtime_dir = os.path.dirname(os.path.abspath(__file__))
        
        # --- DEBUG HOOK ---
        if question == "debug_env":
            files = []
            for root, dirs, ffiles in os.walk(runtime_dir):
                for f in ffiles:
                    files.append(os.path.relpath(os.path.join(root, f), runtime_dir))
            
            scripts_dir = os.path.join(runtime_dir, "scripts")
            loaded = []
            if os.path.exists(scripts_dir):
                for filename in os.listdir(scripts_dir):
                    if filename.endswith(".py"):
                        loaded.append(filename)
            
            import_errors = []
            if os.path.exists(scripts_dir):
                for filename in os.listdir(scripts_dir):
                    if filename.endswith(".py") and not filename.startswith("_"):
                        module_name = filename[:-3]
                        file_path = os.path.join(scripts_dir, filename)
                        try:
                            spec = importlib.util.spec_from_file_location(module_name, file_path)
                            if spec and spec.loader:
                                module = importlib.util.module_from_spec(spec)
                                spec.loader.exec_module(module)
                                func = getattr(module, module_name, None)
                                if func and callable(func):
                                    pass
                                else:
                                    import_errors.append(f"{filename}: function {module_name} not found or not callable")
                        except Exception as e:
                            import_errors.append(f"{filename}: {str(e)}")
            
            import urllib.request
            sa_email = "Unknown"
            try:
                req = urllib.request.Request(
                    "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/email",
                    headers={"Metadata-Flavor": "Google"}
                )
                with urllib.request.urlopen(req, timeout=2) as response:
                    sa_email = response.read().decode("utf-8").strip()
            except Exception as e:
                sa_email = f"Error: {e}"
            
            return f"Active Service Account: {sa_email}\nRuntime Dir: {runtime_dir}\nFiles:\n" + "\n".join(files) + "\nScripts dir contents:\n" + "\n".join(loaded) + "\nImport Errors:\n" + "\n".join(import_errors)
        # --- END DEBUG HOOK ---

        scripts_dir = os.path.join(runtime_dir, "scripts")
        skill_md_path = os.path.join(runtime_dir, "SKILL.md")
        
        # Load the custom system instruction from SKILL.md (overriding default developer prompt)
        if os.path.exists(skill_md_path):
            with open(skill_md_path, "r", encoding="utf-8") as f:
                skill_content = f.read()
            # Strip frontmatter
            content_stripped = re.sub(r"^---.*?---", "", skill_content, flags=re.DOTALL).strip()
            self.config.system_instructions = CustomSystemInstructions(text=content_stripped)
        
        # Load local python scripts as tools
        self.config.tools = load_local_tools(scripts_dir)
        self.config.skills_paths = [runtime_dir]
        self.config.workspaces = []
        
        import hubscape_adk
        user_id = (context or {}).get("userId") or "anonymous_user"
        remote_ctx = hubscape_adk.RemoteContext(user_id=user_id, project_id=self.config.project)
        
        with hubscape_adk.context_session(remote_ctx):
            async with Agent(config=self.config) as agent:
                response = await agent.chat(question)
                await response.resolve()
                return await response.text()

# Singleton instance used as the serialization target
todo_agent_app = TodoAgent()
