# Chapter 7: Advanced Integrations: MCP, A2A, & Secrets

This chapter outlines how custom agents communicate with third-party tools (MCP), interface with other agents (A2A), and access encrypted capabilities and secrets safely.

---

## 1. Model Context Protocol (MCP) Integration

The ADK allows agents to interact with external tools hosted on remote MCP servers (e.g. Jira, GitHub, databases). 

To invoke an MCP tool programmatically inside your tool script:
```python
# app/scripts/create_issue.py
from app.core.hubscape_adk import get_context

async def create_issue(title: str, body: str) -> dict:
    context = get_context()
    
    # Retrieve the whitelisted server config dynamically from raw context
    mcp_config = context.raw_context.get("mcp_servers", {}).get("github_mcp")
    
    mcp_result = await context.mcp.call_tool(
        agent_id=context.agent_id,
        server_name="github_mcp",
        tool_name="create_issue",
        arguments={"title": title, "body": body},
        config=mcp_config,
        context=context
    )
    return mcp_result
```

---

## 2. Agent-to-Agent (A2A) Connections

A2A allows sub-agents to discover and delegate queries to other agents.

### Data Isolation & Whitelisting:
To prevent unauthorized cross-tenant communication:
1. Discovery and consulting operations must work **solely** within the `accessible_agents` list injected into the context at runtime.
2. If an agent tries to call an external tool on an agent not listed in `accessible_agents`, the request must fail immediately.

### Executing A2A Call in Python:
Use the standard context agents wrapper:
```python
# app/scripts/consult_support.py
from app.core.hubscape_adk import get_context

async def consult_support(user_query: str) -> dict:
    context = get_context()
    
    # Delegate standard tool calling
    result = await context.agents.call_external_tool(
        ext_agent_key="support_ticket_agent",
        tool_name="file_ticket",
        arguments={"issue": user_query}
    )
    return result
```

---

## 3. Platform Secrets Vault

Never hardcode credentials or secrets inside repository files.
* **Secrets Retrieval:** Secure keys are injected into the agent context dynamically. Retrieve secrets using the context raw config:
  ```python
  api_key = context.raw_context.get("secrets", {}).get("API_SECRET_KEY") or os.environ.get("API_SECRET_KEY")
  ```
  This ensures compatibility with both the cloud environment secrets vault and local `.env` mock configuration keys.

---

[Next Chapter: GEAP Developer Workflow](CHAPTER_8_GEAP_DEVELOPER_WORKFLOW.md) | [Previous Chapter: Lego Widgets](CHAPTER_6_LEGO_WIDGETS_AND_IFRAMES.md)
