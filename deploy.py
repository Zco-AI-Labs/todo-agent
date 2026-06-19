import os
import vertexai
from vertexai.preview import reasoning_engines
from agent import todo_agent_app

# Resolve environment configuration
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "hubscape-geap")
LOCATION = os.getenv("GCP_LOCATION", "us-central1")
STAGING_BUCKET = os.getenv("GCP_STAGING_BUCKET")

if not STAGING_BUCKET:
    raise ValueError("GCP_STAGING_BUCKET environment variable must be set.")

print(f"Initializing Vertex AI (Project: {PROJECT_ID}, Location: {LOCATION}, Bucket: {STAGING_BUCKET})...")
vertexai.init(project=PROJECT_ID, location=LOCATION, staging_bucket=STAGING_BUCKET)

print("Deploying todo-agent to GEAP Agent Registry...")
reasoning_engine = reasoning_engines.ReasoningEngine.create(
    todo_agent_app,
    requirements=[
        "google-antigravity",
        "google-cloud-aiplatform",
        "cloudpickle==3.0.0"
    ],
    extra_packages=["scripts", "SKILL.md", "agent.py"], # Packages the local skill definition, script tools, and agent class
    display_name="todo-agent",
    description="Managed GEAP agent for user personal to-do lists."
)

print("\n🎉 Deployment Successful!")
print(f"GEAP Resource Name: {reasoning_engine.resource_name}")

# Post-Deployment Cleanup: Delete older deployments of the same agent
try:
    print("\n🧹 Cleaning up older todo-agent deployments on GCP...")
    all_engines = reasoning_engines.ReasoningEngine.list()
    for engine in all_engines:
        if engine.display_name == "todo-agent" and engine.resource_name != reasoning_engine.resource_name:
            print(f"Deleting stale engine instance: {engine.resource_name}...")
            engine.delete()
            print(f"Successfully deleted {engine.resource_name}.")
    print("✨ Cleanup complete!")
except Exception as cleanup_err:
    print(f"⚠️ Non-critical error during old deployment cleanup: {cleanup_err}")

