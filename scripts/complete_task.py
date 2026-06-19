import logging
from datetime import datetime, timezone
import hubscape_adk

logger = logging.getLogger(__name__)

def complete_task(task_id: str) -> dict:
    """Marks a specific task as complete.

    Args:
        task_id: The exact ID of the task to complete (returned from list_tasks).
    """
    context = hubscape_adk.get_context()
    user_id = context.auth.get_user_id()
    logger.info(f"Completing task {task_id} for user {user_id}")
    
    tasks_ref = context.db.collection('platform_users').document(user_id).collection('adk_tasks')
    doc_ref = tasks_ref.document(task_id)
    
    doc = doc_ref.get()
    if not doc.exists:
        return {"error": "Task not found. Please ask the user to verify the task ID."}
        
    doc_ref.update({
        "status": "completed",
        "completed_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {
        "status": "success",
        "message": f"Task '{doc.to_dict().get('name')}' marked as complete."
    }
