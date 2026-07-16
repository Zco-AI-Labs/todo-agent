# Chapter 4: RemoteContext, Scopes, and File Storage

The `RemoteContext` object (retrieved via `get_context()` inside a tool script) is the agent's gateway to the platform's state, user authentication details, Firestore database operations, and Google Cloud Storage (GCS) assets.

---

## 1. Authentication Details (`context.auth`)

Retrieve user and organizational scopes from `context.auth`:
* `context.auth.get_user_id()`: Returns the unique UUID of the active user.
* `context.auth.org_id`: The organization UUID (always populated).
* `context.auth.hub_id`: The active Hub UUID (may be `None` if org-scoped).

---

## 2. Standardized Database Scopes

To enforce strict data isolation between users, organizations, and hubs, Firestore paths are dynamically resolved based on the chosen scope parameter:

* **`user` Scope:** Scoped to the individual user.
  `platform_users/{user_id}/agent_data/{agent_id}/{collection_name}/`
* **`hub` Scope:** Scoped to the active hub (visible to all hub members).
  `organizations/{org_id}/hubs/{hub_id}/agent_data/{agent_id}/{collection_name}/`
* **`org` Scope:** Scoped to the organization.
  `organizations/{org_id}/agent_data/{agent_id}/{collection_name}/`
* **`platform` Scope:** Shared globally by the agent across the platform.
  `agents/{agent_id}/agent_data/platform/{collection_name}/`

### Database Methods on `RemoteContext`:
* `context.save(scope, collection_name, doc_id, data)`: Creates or merges data. Automatically appends audit metadata (`created_by`, `created_at`, `updated_by`, `updated_at`, `version`).
* `context.get(scope, collection_name, doc_id)`: Retrieves a document from the scoped path.
* `context.delete(scope, collection_name, doc_id)`: Deletes the specified document.
* `context.list(scope, collection_name)`: Returns a list of all documents in the collection path.

---

## 3. Persistent File Storage (GCS)

Standard GCS storage is fully integrated via context file methods. Like database scopes, file storage paths are automatically isolated based on the scope parameter:

### File Storage Methods on `RemoteContext`:
* `context.save_file(scope, filename, content, content_type=None)`: Uploads raw binary file content (bytes) to GCS and returns a dictionary containing the GCS storage path and a secure download URL.
* `context.get_file(scope, filename)`: Downloads and returns the binary content (`bytes`) of the file from GCS.
* `context.delete_file(scope, filename)`: Permanently deletes the file from GCS.

---

## 4. Index-Free Query Rules

The platform does not support custom composite indexes in production databases. 
* **Rule:** Do not write queries containing multiple inequality filters, order-by clauses on unindexed fields, or filtering across multiple ranges.
* **Workaround:** If you need complex queries, fetch the list of scoped records into memory using `context.list(scope, collection_name)` and perform sorting, filtering, or slicing programmatically in Python.

---

[Next Chapter: Sandbox Emulation & Parity Details](CHAPTER_5_SANDBOX_EMULATION.md) | [Previous Chapter: Tool Scripts](CHAPTER_3_TOOLS_AND_PROMPTS.md)
