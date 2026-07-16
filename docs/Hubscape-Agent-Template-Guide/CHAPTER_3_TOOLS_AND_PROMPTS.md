# Chapter 3: Tool Scripts & Prompt Structure

This chapter covers how the ADK parses system instructions (prompts) and dynamically constructs LLM tool schemas from standalone Python functions.

---

## 1. Defining System Instructions (`app/SKILL.md`)

System instructions (the agent's persona and rules) are housed inside the markdown file [app/SKILL.md](file:///Users/rajvekeria/Documents/GitHub/hubscape-agent-template/app/SKILL.md).
* **YAML Frontmatter:** The top of the file contains configurations (name, description) that identify the agent:
  ```markdown
  ---
  name: todo_agent
  description: Manages user tasks and schedules.
  ---
  You are a highly efficient to-do list manager...
  ```
* **Auto-Scrubbing:** The ADK loader automatically reads this file, strips the YAML frontmatter, and passes the remaining markdown instructions directly to the `instruction` property of the `google.adk.Agent` model instance in `app/agent.py`.

---

## 2. Implementing Standalone Tool Scripts (`app/scripts/`)

Tools are written as individual, standalone Python files in the `app/scripts/` directory. 

* **Signatures & Schemas:** The function name inside the script must match the filename (e.g., `app/scripts/create_todo.py` must define `async def create_todo(...)`). The ADK automatically parses parameter types, defaults, and docstrings to construct the JSON tool schemas passed to Gemini.
* **Context Handling:** Do not pass the `context` parameter in the tool's function arguments signature. Instead, import and call `get_context()` inside the function body. This keeps the schema definition passed to Gemini clean and free from metadata.
* **No Manual RemoteContext Instantiation:** Do **not** manually instantiate `RemoteContext(...)` or hardcode fallback credentials (e.g., `user_id="dev-user-123"`) inside your tool script body. Tools must rely purely on the active context retrieved via `get_context()`. Manual instantiation bypasses session routing, breaks dynamic multi-user database scoping, and crashes in production where credential-less connections are blocked.

### Example Tool implementation:
```python
# app/scripts/create_todo.py
import logging
from app.core.hubscape_adk import get_context

logger = logging.getLogger(__name__)

async def create_todo(task_title: str, priority: str = "medium") -> dict:
    """
    Creates a new task in the user's to-do list.

    Args:
        task_title: The title/content of the task.
        priority: The priority level ('high', 'medium', 'low').
    """
    logger.info(f"Adding task: {task_title}")
    context = get_context()
    
    # Standard DB save
    result = context.save(
        scope="user",
        collection_name="tasks",
        doc_id=f"task_{task_title}",
        data={"title": task_title, "priority": priority}
    )
    return {"status": "success", "task": result}
```

---

## 3. Decommissioning of Inbound API Routes (`api.py`)

GEAP and sandboxed ADK containers run in secure isolated environments. **Inbound HTTP servers (`api.py`) are fully decommissioned.** Custom inbound routing (like custom web routers or Webhook listeners inside the agent) is not supported.

* **OAuth & Webhooks:** If you need to handle OAuth redirects or external callbacks, route them to the central platform backend. The backend processes the events and saves tokens/data into Firestore scopes.
* **Querying State:** The agent then reads this state from the database at runtime using the scoped database client.
* **Outbound Connections:** Outbound HTTP client calls (using `httpx` or similar) are fully supported. Always set strict timeout controls.

---

[Next Chapter: RemoteContext, Scopes, and File Storage](CHAPTER_4_REMOTE_CONTEXT_AND_DATABASE.md) | [Previous Chapter: Directory Specification](CHAPTER_2_DIRECTORY_SPECIFICATION.md)
