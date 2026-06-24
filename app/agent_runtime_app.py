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

import sys
import os
# Ensure standard imports share the same module instance
app_dir = os.path.dirname(os.path.abspath(__file__))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

import asyncio
import logging
from typing import Any, Optional, Dict, List, Union

import nest_asyncio
import vertexai
from dotenv import load_dotenv
from a2a.types import AgentCapabilities, AgentCard, AgentExtension, TransportProtocol
from a2a.server.agent_execution import RequestContext
from a2a.server.events.event_queue import EventQueue

from google.adk.a2a.executor.a2a_agent_executor import A2aAgentExecutor
from google.adk.a2a.utils.agent_card_builder import AgentCardBuilder
from google.adk.apps import App
from google.adk.artifacts import GcsArtifactService, InMemoryArtifactService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.cloud import logging as google_cloud_logging
from vertexai.preview.reasoning_engines import A2aAgent

import hubscape_adk
from app.agent import app as adk_app
from app.app_utils.telemetry import setup_telemetry
from app.app_utils.typing import Feedback

# Load environment variables from .env file at runtime
load_dotenv()

class AgentEngineA2aExecutor(A2aAgentExecutor):
    """Custom A2A Executor that intercepts requests to inject RemoteContext."""
    async def _handle_request(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ):
        metadata = context.metadata or {}
        import uuid
        
        user_id_resolved = metadata.get("userId") or metadata.get("user_id") or "anonymous_user"
        org_id = metadata.get("orgId") or metadata.get("org_id")
        hub_id = metadata.get("hubId") or metadata.get("hub_id")
        
        agent_uuid = str(uuid.uuid5(uuid.NAMESPACE_URL, "https://github.com/Zco-AI-Labs/todo-agent"))
        project_id = os.getenv("PROJECT_ID") or os.getenv("GCP_PROJECT_ID") or "hubscape-geap"
        
        remote_ctx = hubscape_adk.RemoteContext(
            user_id=user_id_resolved,
            agent_id=agent_uuid,
            org_id=org_id,
            hub_id=hub_id,
            project_id=project_id,
            raw_context=metadata
        )
        
        # Enter the context session to ensure all Firestore calls in tools are authenticated
        with hubscape_adk.context_session(remote_ctx):
            await super()._handle_request(context, event_queue)


class AgentEngineApp(A2aAgent):
    @staticmethod
    def create(
        app: App | None = None,
        artifact_service: Any = None,
        session_service: Any = None,
    ) -> Any:
        if app is None:
            app = adk_app

        def create_runner() -> Runner:
            return Runner(
                app=app,
                session_service=session_service,
                artifact_service=artifact_service,
            )

        try:
            asyncio.get_running_loop()
            nest_asyncio.apply()
        except RuntimeError:
            pass

        agent_card = asyncio.run(AgentEngineApp.build_agent_card(app=app))

        return AgentEngineApp(
            agent_executor_builder=lambda: AgentEngineA2aExecutor(runner=create_runner()),
            agent_card=agent_card,
        )

    @staticmethod
    async def build_agent_card(app: App) -> AgentCard:
        agent_card_builder = AgentCardBuilder(
            agent=app.root_agent,
            capabilities=AgentCapabilities(
                streaming=False,
                extensions=[
                    AgentExtension(
                        uri="https://google.github.io/adk-docs/a2a/a2a-extension/",
                        description="Ability to use the new agent executor implementation",
                    ),
                ],
            ),
            rpc_url="http://localhost:9999/",
            agent_version=os.getenv("AGENT_VERSION", "0.1.0"),
        )
        agent_card = await agent_card_builder.build()
        agent_card.preferred_transport = TransportProtocol.http_json  # Http Only.
        agent_card.supports_authenticated_extended_card = True
        return agent_card

    def set_up(self) -> None:
        """Initialize the agent engine app with logging and telemetry."""
        # Explicitly pop GOOGLE_GENAI_USE_ENTERPRISE and set GOOGLE_GENAI_USE_VERTEXAI to force regional Vertex AI routing
        os.environ.pop("GOOGLE_GENAI_USE_ENTERPRISE", None)
        os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"
        if gemini_location:
            os.environ["GOOGLE_CLOUD_LOCATION"] = gemini_location
        vertexai.init()
        setup_telemetry()
        super().set_up()
        logging.basicConfig(level=logging.INFO)
        logging_client = google_cloud_logging.Client()
        self.logger = logging_client.logger(__name__)

    def register_feedback(self, feedback: dict[str, Any]) -> None:
        """Collect and log feedback."""
        feedback_obj = Feedback.model_validate(feedback)
        self.logger.log_struct(feedback_obj.model_dump(), severity="INFO")

    def register_operations(self) -> dict[str, list[str]]:
        """Registers the operations of the Agent."""
        operations = super().register_operations()
        operations[""] = [*operations.get("", []), "register_feedback"]
        return operations

    def clone(self) -> "AgentEngineApp":
        """Returns a clone of the Agent Runtime application."""
        return self


gemini_location = os.environ.get("GOOGLE_CLOUD_LOCATION")
logs_bucket_name = os.environ.get("LOGS_BUCKET_NAME")
agent_runtime = AgentEngineApp.create(
    app=adk_app,
    artifact_service=(
        GcsArtifactService(bucket_name=logs_bucket_name)
        if logs_bucket_name
        else InMemoryArtifactService()
    ),
    session_service=InMemorySessionService(),
)
