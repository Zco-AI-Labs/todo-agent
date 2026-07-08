import pytest
from unittest.mock import MagicMock, patch
import hubscape_adk
from app.scripts.add_task import add_task
from app.scripts.list_tasks import list_tasks
from app.scripts.add_platform_reminder import add_platform_reminder
from app.scripts.list_platform_reminders import list_platform_reminders

def test_adk_platform_scope_db_path():
    ctx = hubscape_adk.RemoteContext(
        user_id="user123",
        agent_id="todo-agent"
    )
    
    path = ctx.get_agent_db_path(scope="platform", collection_name="submissions", doc_id="doc456")
    assert path == "agents/todo-agent/agent_data/platform/submissions/doc456"

def test_adk_storage_paths():
    ctx = hubscape_adk.RemoteContext(
        user_id="user123",
        agent_id="todo-agent",
        hub_id="hub123",
        org_id="org123"
    )
    
    p_path = ctx.get_agent_storage_path(scope="platform", filename="img.png")
    assert p_path == "agents/todo-agent/platform/img.png"
    
    u_path = ctx.get_agent_storage_path(scope="user", filename="img.png")
    assert u_path == "agents/todo-agent/user/user123/img.png"
    
    h_path = ctx.get_agent_storage_path(scope="hub", filename="img.png")
    assert h_path == "agents/todo-agent/hub/hub123/img.png"
    
    o_path = ctx.get_agent_storage_path(scope="org", filename="img.png")
    assert o_path == "agents/todo-agent/org/org123/img.png"

@patch("google.cloud.storage.Client")
def test_adk_save_get_delete_file(mock_gcs_client):
    ctx = hubscape_adk.RemoteContext(
        user_id="user123",
        agent_id="todo-agent",
        project_id="test-project",
        raw_context={"storageBucket": "my-bucket"}
    )
    
    mock_client_inst = MagicMock()
    mock_gcs_client.return_value = mock_client_inst
    
    mock_bucket = MagicMock()
    mock_bucket.name = "my-bucket"
    mock_client_inst.bucket.return_value = mock_bucket
    
    mock_blob = MagicMock()
    mock_bucket.blob.return_value = mock_blob
    
    # Save file
    res = ctx.save_file(scope="platform", filename="test.txt", content=b"hello world", content_type="text/plain")
    assert res["storage_path"] == "agents/todo-agent/platform/test.txt"
    assert "download_url" in res
    assert "alt=media" in res["download_url"]
    mock_bucket.blob.assert_called_with("agents/todo-agent/platform/test.txt")
    mock_blob.upload_from_string.assert_called_once_with(b"hello world", content_type="text/plain")
    
    # Get file
    mock_blob.exists.return_value = True
    mock_blob.download_as_bytes.return_value = b"hello world"
    file_bytes = ctx.get_file(scope="platform", filename="test.txt")
    assert file_bytes == b"hello world"
    mock_blob.download_as_bytes.assert_called_once()
    
    # Delete file
    ctx.delete_file(scope="platform", filename="test.txt")
    mock_blob.delete.assert_called_once()


def test_add_and_list_tasks():
    # Setup context and mock database and storage operations
    ctx = hubscape_adk.RemoteContext(
        user_id="user123",
        agent_id="todo-agent",
        project_id="test-project"
    )
    
    mock_db = MagicMock()
    ctx._db = mock_db
    
    # Mock save_file
    mock_save_file = MagicMock(return_value={"download_url": "https://dummy/test.jpg"})
    ctx.save_file = mock_save_file
    
    # Executing tool inside context session
    with hubscape_adk.context_session(ctx):
        res = add_task("Buy groceries")
        assert res["status"] == "success"
        assert res["image_url"] == "https://dummy/test.jpg"
        
        # Verify save called on DB
        mock_db.document.assert_called()
        
        # Mock list to return the task with image_url
        mock_list = MagicMock(return_value=[
            {
                "id": "task123",
                "name": "Buy groceries",
                "status": "open",
                "image_url": "https://dummy/test.jpg"
            }
        ])
        ctx.list = mock_list
        
        list_res = list_tasks()
        assert list_res["status"] == "success"
        assert len(list_res["tasks"]) == 1
        assert list_res["tasks"][0]["image_url"] == "https://dummy/test.jpg"


def test_platform_reminders():
    ctx = hubscape_adk.RemoteContext(
        user_id="user123",
        agent_id="todo-agent",
        project_id="test-project"
    )
    
    mock_db = MagicMock()
    ctx._db = mock_db
    
    with hubscape_adk.context_session(ctx):
        # Add reminder
        res = add_platform_reminder("Maintain dilithium crystals")
        assert res["status"] == "success"
        assert "reminder_id" in res
        
        # Verify db.document was called with "agents/todo-agent/agent_data/platform/reminders" path
        called_args = mock_db.document.call_args[0][0]
        assert "agents/todo-agent/agent_data/platform/reminders" in called_args
        
        # Mock list reminders
        mock_list = MagicMock(return_value=[
            {
                "id": "rem123",
                "name": "Maintain dilithium crystals",
                "status": "open"
            }
        ])
        ctx.list = mock_list
        
        list_res = list_platform_reminders()
        assert list_res["status"] == "success"
        assert len(list_res["reminders"]) == 1
        assert list_res["reminders"][0]["name"] == "Maintain dilithium crystals"
