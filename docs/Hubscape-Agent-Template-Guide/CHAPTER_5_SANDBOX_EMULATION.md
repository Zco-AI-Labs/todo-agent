# Chapter 5: Sandbox Emulation & Parity Details

This chapter covers the relationship between the `hubscape-agent-template` workspace and the `hubscape-adk-studio` runner, explaining how standard database and storage interfaces are emulated locally.

---

## 1. Local Emulation Architecture

To allow offline prototyping, the `hubscape-adk` local CLI starts a mock platform core (called Holodeck) that executes your agent code locally. 

When running in local dev, your agent is not connected to a live GCP Firestore database or a GCS Bucket. To protect production and let tools operate seamlessly, the local sandbox dynamically intercepts database and storage calls.

---

## 2. Runtime Monkeypatching (How it Works)

When you boot the sandbox via `hubscape-adk`, the runner loads your agent code and applies a series of runtime patches using the monkeypatching system:

```text
Local Client Request               Sandbox Runtime Interception           Mock File Persistence
--------------------               ----------------------------           ---------------------
context.save(...)        ----->    mock_save()                    ----->  Writes to local_db.json
context.get(...)         ----->    mock_get()                     ----->  Reads from local_db.json
context.save_file(...)   ----->    mock_save_file()               ----->  Writes to local storage folder
```

* **Firestore Emulation:** The sandbox intercepts calls to standard methods like `context.save()` and `context.get()`. It redirects these calls to private mock endpoints (`save_agent_data` and `get_agent_data`) that read and write directly to a local JSON file (`local_db.json`) in your root workspace.
* **GCS Emulation:** Calls to `context.save_file()` are intercepted and routed to `save_agent_file`. It writes the file directly to your local sandbox storage directory and returns a local relative download URL.

---

## 3. Strict Parity Guidelines (Critical Pitfalls)

To ensure that your agent functions perfectly in production, you must adhere to the following rules:

### Rule 1: Use Standard Public Methods Only
Do **not** call private sandbox implementation methods directly in your tool scripts.
* **Incorrect:** `context.save_agent_data(...)` or `context.get_agent_data(...)`
* **Correct:** `context.save(...)` or `context.get(...)`
* **Why:** Calling private methods directly works in the local sandbox because they are exposed by the test runner. However, these methods do not exist on the real `RemoteContext` class in production, and your agent will throw an `AttributeError` and crash on the live cloud server.

### Rule 2: Exclude Heavy Binary Payloads from the Database
When saving document data to Firestore (using `context.save()`), do not include large Base64-encoded strings (such as full preview images).
* **Why:** Local databases may handle large payloads, but writing 5MB+ strings into a Firestore document will result in serialization timeouts and exceed database document size limits. Save the file to GCS using `context.save_file()` and store only the resulting download URL in the database document.

### Rule 3: Avoid Manual Context Creation (No Hardcoded Fallbacks)
Never manually instantiate `RemoteContext` or hardcode fallback credentials (such as `user_id="dev-user-123"`) inside agent tool scripts.
* **Why:** Hardcoding fallbacks locks database operations to a single mock user, making it impossible to locally test multi-user scenarios, verify cross-org collaboration features, or audit Hub Data Isolation rules. 
* **The Correct Pattern:** Always invoke `get_context()` and assume it is executed inside a live session. If you need to simulate tools for testing outside of a running chat session, do so within your test suite using the standard `context_session` manager.

---

[Next Chapter: Lego Widgets & Sandboxed IFrames](CHAPTER_6_LEGO_WIDGETS_AND_IFRAMES.md) | [Previous Chapter: RemoteContext](CHAPTER_4_REMOTE_CONTEXT_AND_DATABASE.md)
