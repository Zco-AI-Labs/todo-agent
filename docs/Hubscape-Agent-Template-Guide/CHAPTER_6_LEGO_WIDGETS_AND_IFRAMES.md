# Chapter 6: Lego Widgets & Sandboxed IFrames

Custom agents can display rich interfaces inside the companion chat UI. Simple forms are built using declarative JSON (Lego Widgets), while complex visuals (such as poster compositors or canvas editors) use custom HTML iframes.

---

## 1. Declarative Lego Widgets

Lego widgets are JSON files representing a tree of nested components. They must be saved inside:
`app/ui/widgets/<widget_name>.json`

### Data Binding Rules:
1. **Flat Keys:** The React UI parser flattens variables passed to widgets. Reference keys directly (e.g. use `{{image_url}}` rather than `{{data.image_url}}`).
2. **No Dot Notation:** Variable placeholders are parsed using the regex pattern `/\{\{\s*(\w+)\s*\}\}/g`. Because dots (`.`) are not word characters, placeholders containing dots will fail to parse and render literally in the DOM.

---

## 2. Visual Sandboxed IFrames (`iframe`)

For complex UIs requiring canvas interactions, dragging, or real-time editing, use the `iframe` Lego component to embed custom HTML files:

```json
{
  "type": "iframe",
  "props": {
    "src": "/api/agents/{{agent_id}}/static/my_widget.html",
    "className": "w-full h-[600px] border-0 rounded-xl"
  }
}
```

* **Relative Src Rule:** Always use relative platform paths (e.g. `/api/agents/{{agent_id}}/static/widget.html`) inside the `src` property. Never hardcode absolute URLs or ports (like `http://localhost:8090/...`) as they will fail when deployed to production cloud routing.

---

## 3. Bidirectional IFrame Communication

Because GEAP/ADK agent containers are sandboxed, iframes cannot directly send HTTP requests (`fetch` or `Axios`) to custom agent API routes. Instead, they communicate using standard HTML5 browser messages:

```text
  Custom HTML (IFrame)                 Hubscape Chat UI                     Agent Container
------------------------               ----------------                     ---------------
window.parent.postMessage()  ----->    Intercepts Submit       ----->       Executes Python Tool
                                       Sends HTTP POST                      (e.g., generate_qr)
IFrame Message Listener      <-----    Returns tool response   <-----       Returns JSON Dict
```

### 1. Sending an Action from inside the IFrame
When the user clicks a button inside your HTML page, post a message containing the tool name and payload arguments to the parent window:
```javascript
// Extract dynamic agent ID from window pathname
const pathParts = window.location.pathname.split('/');
const agentId = ((pathParts[2] === 'plugins' || pathParts[2] === 'agents') && pathParts[3]) ? pathParts[3] : 'my_agent';

window.parent.postMessage({
  type: 'SUBMIT_FORM',
  actionUrl: `agent://${agentId}/my_backend_tool`,
  payload: { param1: 'value1' }
}, '*');
```

### 2. Processing the Response
The parent Hubscape container captures this request, executes the corresponding Python tool script (e.g., `app/scripts/my_backend_tool.py`), and posts the tool's JSON output back to the iframe. Listen for this response in your HTML JavaScript:
```javascript
window.addEventListener('message', (event) => {
  const data = event.data;
  if (data && data.type === 'TOOL_RESPONSE') {
    console.log("Received data from Python script:", data.payload);
    // Update HTML DOM visually
  }
});
```

---

[Next Chapter: Advanced Integrations](CHAPTER_7_ADVANCED_INTEGRATIONS.md) | [Previous Chapter: Sandbox Emulation](CHAPTER_5_SANDBOX_EMULATION.md)
