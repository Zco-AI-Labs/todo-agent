import logging
import traceback
import hubscape_adk

logger = logging.getLogger(__name__)

@hubscape_adk.require_tool_privilege
def add_platform_reminder(reminder_text: str) -> dict:
    """Adds a new platform reminder visible to all users of the platform.

    Args:
        reminder_text: The description/text of the reminder to add.
    """
    try:
        context = hubscape_adk.get_context()
        logger.info(f"Adding platform reminder: '{reminder_text}'")
        
        import uuid
        reminder_id = uuid.uuid4().hex
        
        context.save(
            scope="platform",
            collection_name="reminders",
            doc_id=reminder_id,
            data={
                "name": reminder_text,
                "status": "open"
            }
        )
        
        return {
            "status": "success",
            "message": f"Platform reminder '{reminder_text}' added successfully.",
            "reminder_id": reminder_id
        }
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"Error adding platform reminder: {e}\n{tb}")
        return {
            "status": "error",
            "message": f"Failed to add platform reminder: {str(e)}",
            "traceback": tb
        }
