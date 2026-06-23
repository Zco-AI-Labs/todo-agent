import logging
from datetime import datetime, timezone
import traceback
import hubscape_adk

logger = logging.getLogger(__name__)

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
        tb = traceback.format_exc()
        logger.error(f"Error completing task: {e}\n{tb}")
        return {
            "status": "error",
            "message": f"Failed to complete task: {str(e)}",
            "traceback": tb
        }
