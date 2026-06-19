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
        "google-antigravity-sdk",
        "google-cloud-aiplatform",
        "cloudpickle==3.0.0"
    ],
    extra_packages=["scripts", "SKILL.md"], # Packages the local skill definition and script tools
    display_name="todo-agent",
    description="Managed GEAP agent for user personal to-do lists."
)

print("\n🎉 Deployment Successful!")
print(f"GEAP Resource Name: {reasoning_engine.resource_name}")
