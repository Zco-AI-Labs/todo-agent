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
        
        tasks_ref = context.db.collection('platform_users').document(user_id).collection('adk_tasks')
        docs = tasks_ref.where("status", "==", "open").stream()
        
        tasks = []
        for doc in docs:
            data = doc.to_dict()
            tasks.append({
                "task_id": doc.id,
                "name": data.get("name"),
                "created_at": data.get("created_at")
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
