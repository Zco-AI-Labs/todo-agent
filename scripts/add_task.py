import logging
from datetime import datetime, timezone
import hubscape_adk

logger = logging.getLogger(__name__)

def add_task(task_name: str) -> dict:
    """Adds a new task to the user's to-do list.

    Args:
        task_name: The description or name of the task to add.
    """
    context = hubscape_adk.get_context()
    user_id = context.auth.get_user_id()
    logger.info(f"Adding task '{task_name}' for user {user_id}")
    
    tasks_ref = context.db.collection('platform_users').document(user_id).collection('adk_tasks')
    _, doc_ref = tasks_ref.add({
        "name": task_name,
        "status": "open",
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {
        "status": "success",
        "message": f"Task '{task_name}' added successfully.",
        "task_id": doc_ref.id
    }
