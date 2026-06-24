# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import logging
import os
from typing import Any, Optional, Dict, List, Union

import vertexai
from dotenv import load_dotenv
from google.adk.artifacts import GcsArtifactService, InMemoryArtifactService
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.cloud import logging as google_cloud_logging
from vertexai.agent_engines.templates.adk import AdkApp

from app.agent import app as adk_app
from app.app_utils.telemetry import setup_telemetry
from app.app_utils.typing import Feedback

# Load environment variables from .env file at runtime
load_dotenv()


class AgentEngineApp(AdkApp):
    def set_up(self) -> None:
        """Initialize the agent engine app with logging and telemetry."""
        vertexai.init()
        setup_telemetry()
        super().set_up()
        # Explicitly pop GOOGLE_GENAI_USE_ENTERPRISE to force regional Vertex AI routing
        os.environ.pop("GOOGLE_GENAI_USE_ENTERPRISE", None)
        logging.basicConfig(level=logging.INFO)
        logging_client = google_cloud_logging.Client()
        self.logger = logging_client.logger(__name__)
        if gemini_location:
            os.environ["GOOGLE_CLOUD_LOCATION"] = gemini_location

    def register_feedback(self, feedback: dict[str, Any]) -> None:
        """Collect and log feedback."""
        feedback_obj = Feedback.model_validate(feedback)
        self.logger.log_struct(feedback_obj.model_dump(), severity="INFO")

    def query(self, question: str, context: Optional[dict] = None) -> str:
        """Non-streaming query delegation to TodoAgent."""
        import asyncio
        import concurrent.futures
        from app.agent import todo_agent_app
        
        async def run_query():
            return await todo_agent_app.query(question, context)
            
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                return executor.submit(lambda: asyncio.run(run_query())).result()
        else:
            return asyncio.run(run_query())

    def stream_query(self, *, message, user_id: str, session_id=None, run_config=None, **kwargs):
        """Override to initialize RemoteContext and inject dynamic system instructions."""
        context = kwargs.pop("context", None)
        
        import uuid
        from app import hubscape_adk
        from app.agent import root_agent
        
        user_id_resolved = (context or {}).get("userId") or (context or {}).get("user_id") or user_id or "anonymous_user"
        org_id = (context or {}).get("orgId") or (context or {}).get("org_id")
        hub_id = (context or {}).get("hubId") or (context or {}).get("hub_id")
        
        agent_uuid = str(uuid.uuid5(uuid.NAMESPACE_URL, "https://github.com/Zco-AI-Labs/todo-agent"))
        project_id = os.getenv("PROJECT_ID") or os.getenv("GCP_PROJECT_ID") or "hubscape-geap"
        
        remote_ctx = hubscape_adk.RemoteContext(
            user_id=user_id_resolved,
            agent_id=agent_uuid,
            org_id=org_id,
            hub_id=hub_id,
            project_id=project_id,
            raw_context=context
        )
        
        system_instruction = (context or {}).get("system_instruction")
        if system_instruction:
            root_agent.instruction = system_instruction

        session_id_resolved = session_id or (context or {}).get("sessionId") or f"session_{user_id_resolved}_{hub_id}"

        with hubscape_adk.context_session(remote_ctx):
            yield from super().stream_query(
                message=message,
                user_id=user_id,
                session_id=session_id_resolved,
                run_config=run_config,
                **kwargs,
            )

    async def async_stream_query(self, *, message, user_id: str, session_id=None, session_events=None, run_config=None, **kwargs):
        """Override to initialize RemoteContext and inject dynamic system instructions."""
        context = kwargs.pop("context", None)
        
        import uuid
        from app import hubscape_adk
        from app.agent import root_agent
        
        user_id_resolved = (context or {}).get("userId") or (context or {}).get("user_id") or user_id or "anonymous_user"
        org_id = (context or {}).get("orgId") or (context or {}).get("org_id")
        hub_id = (context or {}).get("hubId") or (context or {}).get("hub_id")
        
        agent_uuid = str(uuid.uuid5(uuid.NAMESPACE_URL, "https://github.com/Zco-AI-Labs/todo-agent"))
        project_id = os.getenv("PROJECT_ID") or os.getenv("GCP_PROJECT_ID") or "hubscape-geap"
        
        remote_ctx = hubscape_adk.RemoteContext(
            user_id=user_id_resolved,
            agent_id=agent_uuid,
            org_id=org_id,
            hub_id=hub_id,
            project_id=project_id,
            raw_context=context
        )
        
        system_instruction = (context or {}).get("system_instruction")
        if system_instruction:
            root_agent.instruction = system_instruction

        session_id_resolved = session_id or (context or {}).get("sessionId") or f"session_{user_id_resolved}_{hub_id}"

        with hubscape_adk.context_session(remote_ctx):
            async for event in super().async_stream_query(
                message=message,
                user_id=user_id,
                session_id=session_id_resolved,
                session_events=session_events,
                run_config=run_config,
                **kwargs,
            ):
                yield event

    def register_operations(self) -> dict[str, list[str]]:
        """Registers the operations of the Agent."""
        operations = super().register_operations()
        operations[""] = [*operations.get("", []), "register_feedback", "query"]
        return operations

    def clone(self) -> "AgentEngineApp":
        """Returns a clone of the Agent Runtime application."""
        return self


gemini_location = os.environ.get("GOOGLE_CLOUD_LOCATION")
logs_bucket_name = os.environ.get("LOGS_BUCKET_NAME")
agent_runtime = AgentEngineApp(
    app=adk_app,
    artifact_service_builder=lambda: (
        GcsArtifactService(bucket_name=logs_bucket_name)
        if logs_bucket_name
        else InMemoryArtifactService()
    ),
    session_service_builder=lambda: InMemorySessionService(),
)
