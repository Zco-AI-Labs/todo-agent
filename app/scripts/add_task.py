import logging
from datetime import datetime, timezone
import traceback
import hubscape_adk

logger = logging.getLogger(__name__)

@hubscape_adk.require_tool_privilege
def add_task(task_name: str) -> dict:
    """Adds a new task to the user's to-do list.

    Args:
        task_name: The description or name of the task to add.
    """
    try:
        context = hubscape_adk.get_context()
        user_id = context.auth.get_user_id()
        logger.info(f"Adding task '{task_name}' for user {user_id}")
        
        import uuid
        task_id = uuid.uuid4().hex
        context.save(
            scope="user",
            collection_name="tasks",
            doc_id=task_id,
            data={
                "name": task_name,
                "status": "open"
            }
        )
        
        return {
            "status": "success",
            "message": f"Task '{task_name}' added successfully.",
            "task_id": task_id
        }
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"Error adding task: {e}\n{tb}")
        return {
            "status": "error",
            "message": f"Failed to add task: {str(e)}",
            "traceback": tb
        }
