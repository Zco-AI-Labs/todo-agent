import pytest
from unittest.mock import patch, MagicMock
import os
import sys

# Ensure app is in path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "app"))

from core.hubscape_adk import RemoteContext

def test_otp_local_simulation():
    # When K_SERVICE is not in environment, and backend_url is not set
    # It should trigger local dev bypass
    with patch.dict(os.environ, {}):
        if "K_SERVICE" in os.environ:
            del os.environ["K_SERVICE"]
            
        ctx = RemoteContext(user_id="test_user", agent_id="test_agent")
        
        # Test send_otp simulation
        send_res = ctx.send_otp("+15555555555")
        assert send_res["success"] is True
        assert send_res["status"] == "simulated"
        assert "123456" in send_res["message"]
        
        # Test verify_otp simulation (correct code)
        verify_success = ctx.verify_otp("+15555555555", "123456")
        assert verify_success["success"] is True
        assert verify_success["status"] == "verified"
        
        # Test verify_otp simulation (incorrect code)
        verify_fail = ctx.verify_otp("+15555555555", "999999")
        assert verify_fail["success"] is False
        assert verify_fail["status"] == "invalid"

@patch("httpx.post")
def test_otp_cloud_execution(mock_post):
    # Setup mock response
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"success": True, "status": "sent"}
    mock_post.return_value = mock_resp
    
    # Force cloud env via environment variable
    with patch.dict(os.environ, {"K_SERVICE": "yes", "HUBSCAPE_BACKEND_URL": "https://api.hubscape.example.com"}):
        ctx = RemoteContext(
            user_id="test_user", 
            agent_id="test_agent",
            raw_context={"capability_token": "mock_jwt_token"}
        )
        
        res = ctx.send_otp("+15555555555")
        assert res["success"] is True
        assert res["status"] == "sent"
        
        # Verify httpx call structure
        mock_post.assert_called_once_with(
            "https://api.hubscape.example.com/api/otp/send",
            json={"phone_number": "+15555555555", "agent_id": "test_agent"},
            headers={"Authorization": "Bearer mock_jwt_token"},
            timeout=10.0
        )

@patch("httpx.post")
def test_otp_verification_cloud_execution(mock_post):
    # Setup mock response
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"success": True, "status": "verified"}
    mock_post.return_value = mock_resp
    
    # Force cloud env via environment variable
    with patch.dict(os.environ, {"K_SERVICE": "yes", "HUBSCAPE_BACKEND_URL": "https://api.hubscape.example.com"}):
        ctx = RemoteContext(
            user_id="test_user", 
            agent_id="test_agent",
            raw_context={"capability_token": "mock_jwt_token"}
        )
        
        res = ctx.verify_otp("+15555555555", "123456")
        assert res["success"] is True
        assert res["status"] == "verified"
        
        # Verify httpx call structure
        mock_post.assert_called_once_with(
            "https://api.hubscape.example.com/api/otp/verify",
            json={"phone_number": "+15555555555", "code": "123456", "agent_id": "test_agent"},
            headers={"Authorization": "Bearer mock_jwt_token"},
            timeout=10.0
        )
