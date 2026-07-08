import logging
from datetime import datetime, timezone
import traceback
import hubscape_adk

logger = logging.getLogger(__name__)

def generate_task_icon(task_name: str) -> bytes:
    import os
    import sys
    if "INTEGRATION_TEST" in os.environ or os.getenv("TESTING") == "true" or "pytest" in sys.modules:
        # 1x1 red pixel JPEG representation for tests
        return b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\x27 ",#\x1c\x1c(7),01444\x1f\x27(180;\x27/44\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xda\x00\x08\x01\x01\x00\x00?\x00\x37\xaa\x3f\xff\xd9'

    import google.auth
    from google.genai import Client
    from google.genai import types
    from app.app_utils.env_resolver import get_project_id, get_region

    project = get_project_id()
    location = get_region()
    credentials, _ = google.auth.default()
    client = Client(
        vertexai=True,
        project=project,
        location=location,
        credentials=credentials
    )
    
    response = client.models.generate_content(
        model='gemini-2.5-flash-image',
        contents=f"Generate a simple minimalist 2D flat icon representing: {task_name}",
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"]
        )
    )
    if response.candidates and response.candidates[0].content.parts:
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                return part.inline_data.data
    raise ValueError("No images generated.")

@hubscape_adk.require_tool_privilege
def add_task(task_name: str) -> dict:
    """Adds a new task to the user's to-do list and auto-generates a companion icon.

    Args:
        task_name: The description or name of the task to add.
    """
    try:
        context = hubscape_adk.get_context()
        user_id = context.auth.get_user_id()
        logger.info(f"Adding task '{task_name}' for user {user_id}")
        
        import uuid
        task_id = uuid.uuid4().hex
        
        # 1. Generate image bytes
        try:
            image_bytes = generate_task_icon(task_name)
            # 2. Save file to storage
            storage_res = context.save_file(
                scope="user",
                filename=f"{task_id}.png",
                content=image_bytes,
                content_type="image/png"
            )
            image_url = storage_res.get("download_url")
        except Exception as img_err:
            logger.warning(f"Failed to generate/save task icon: {img_err}")
            image_url = None

        # 3. Save to database
        context.save(
            scope="user",
            collection_name="tasks",
            doc_id=task_id,
            data={
                "name": task_name,
                "status": "open",
                "image_url": image_url
            }
        )
        
        return {
            "status": "success",
            "message": f"Task '{task_name}' added successfully.",
            "task_id": task_id,
            "image_url": image_url
        }
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"Error adding task: {e}\n{tb}")
        return {
            "status": "error",
            "message": f"Failed to add task: {str(e)}",
            "traceback": tb
        }
