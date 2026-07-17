import logging
from datetime import datetime, timezone
import traceback
from app.core import hubscape_adk

logger = logging.getLogger(__name__)

@hubscape_adk.require_tool_privilege
def complete_task(task_id: str) -> dict:
    """Marks a specific task as complete.

    Args:
        task_id: The exact ID of the task to complete (returned from list_tasks).
    """
    try:
        context = hubscape_adk.get_context()
        user_id = context.auth.get_user_id()
        logger.info(f"Completing task {task_id} for user {user_id}")
        
        task = context.get("user", "tasks", task_id)
        if not task:
            return {"error": "Task not found. Please ask the user to verify the task ID."}
            
        import datetime
        context.save(
            scope="user",
            collection_name="tasks",
            doc_id=task_id,
            data={
                "status": "completed",
                "completed_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }
        )
        
        return {
            "status": "success",
            "message": f"Task '{task.get('name')}' marked as complete."
        }
    except Exception as e:
        logger.exception("Error completing task")
        return {
            "status": "error",
            "message": f"Failed to complete task: {str(e)}"
        }
