import logging
import traceback
import hubscape_adk

logger = logging.getLogger(__name__)

def list_tasks() -> dict:
    """Retrieves all currently open (incomplete) tasks for the user."""
    try:
        context = hubscape_adk.get_context()
        user_id = context.auth.get_user_id()
        logger.info(f"Listing tasks for user {user_id}")
        
        all_tasks = context.list(scope="user", collection_name="tasks")
        tasks = []
        for task in all_tasks:
            if task.get("status") == "open":
                tasks.append({
                    "task_id": task["id"],
                    "name": task.get("name"),
                    "created_at": task.get("created_at")
                })
            
        if not tasks:
            return {"status": "success", "message": "You have no open tasks!"}
            
        return {
            "status": "success",
            "tasks": tasks
        }
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"Error listing tasks: {e}\n{tb}")
        return {
            "status": "error",
            "message": f"Failed to list tasks: {str(e)}",
            "traceback": tb
        }
