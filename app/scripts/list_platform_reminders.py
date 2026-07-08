import logging
import traceback
import hubscape_adk

logger = logging.getLogger(__name__)

@hubscape_adk.require_tool_privilege
def list_platform_reminders() -> dict:
    """Retrieves all currently active platform-wide reminders."""
    try:
        context = hubscape_adk.get_context()
        logger.info("Listing platform reminders")
        
        all_reminders = context.list(scope="platform", collection_name="reminders")
        reminders = []
        for rem in all_reminders:
            if rem.get("status") == "open":
                reminders.append({
                    "reminder_id": rem["id"],
                    "name": rem.get("name"),
                    "created_at": rem.get("created_at")
                })
            
        if not reminders:
            return {"status": "success", "message": "There are no platform reminders!"}
            
        return {
            "status": "success",
            "reminders": reminders
        }
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"Error listing platform reminders: {e}\n{tb}")
        return {
            "status": "error",
            "message": f"Failed to list platform reminders: {str(e)}",
            "traceback": tb
        }
