"""
Tests for VM console operations.
"""

import pytest
from unittest.mock import Mock, patch

from proxmox_mcp.tools.console.manager import VMConsoleManager

@pytest.fixture
def mock_proxmox():
    """Fixture to create a mock ProxmoxAPI instance."""
    mock = Mock()
    # Setup chained mock calls
    mock.nodes.return_value.qemu.return_value.status.current.get.return_value = {
        "status": "running"
    }
    
    # Setup agent exec endpoint correctly - it's called as endpoint("exec").post()
    mock_agent = Mock()
    mock_exec_endpoint = Mock()
    mock_exec_endpoint.post.return_value = {"pid": 12345}
    mock_agent.return_value = mock_exec_endpoint
    
    # Setup exec-status endpoint - it's called as endpoint("exec-status").get()
    mock_status_endpoint = Mock()
    mock_status_endpoint.get.return_value = {
        "out-data": "command output",
        "err-data": "",
        "exitcode": 0,
        "exited": 1
    }
    
    # Configure the agent to return different endpoints based on the call
    def agent_side_effect(endpoint_name):
        if endpoint_name == "exec":
            return mock_exec_endpoint
        elif endpoint_name == "exec-status":
            return mock_status_endpoint
        return Mock()
    
    mock.nodes.return_value.qemu.return_value.agent.side_effect = agent_side_effect
    return mock

@pytest.fixture
def vm_console(mock_proxmox):
    """Fixture to create a VMConsoleManager instance."""
    return VMConsoleManager(mock_proxmox)

@pytest.mark.asyncio
async def test_execute_command_success(vm_console, mock_proxmox):
    """Test successful command execution."""
    result = await vm_console.execute_command("node1", "100", "ls -l")

    assert result["success"] is True
    assert result["output"] == "command output"
    assert result["error"] == ""
    assert result["exit_code"] == 0

    # Verify correct API calls
    mock_proxmox.nodes.return_value.qemu.assert_called_with("100")
    mock_proxmox.nodes.return_value.qemu.return_value.agent.assert_any_call("exec")
    mock_proxmox.nodes.return_value.qemu.return_value.agent.assert_any_call("exec-status")

@pytest.mark.asyncio
async def test_execute_command_vm_not_running(vm_console, mock_proxmox):
    """Test command execution on stopped VM."""
    mock_proxmox.nodes.return_value.qemu.return_value.status.current.get.return_value = {
        "status": "stopped"
    }

    with pytest.raises(ValueError, match="not running"):
        await vm_console.execute_command("node1", "100", "ls -l")

@pytest.mark.asyncio
async def test_execute_command_vm_not_found(vm_console, mock_proxmox):
    """Test command execution on non-existent VM."""
    mock_proxmox.nodes.return_value.qemu.return_value.status.current.get.side_effect = \
        Exception("VM not found")

    with pytest.raises(ValueError, match="not found"):
        await vm_console.execute_command("node1", "100", "ls -l")

@pytest.mark.asyncio
async def test_execute_command_failure(vm_console, mock_proxmox):
    """Test command execution failure."""
    # Setup agent side effect to raise exception on exec
    def agent_side_effect(endpoint_name):
        if endpoint_name == "exec":
            mock_exec_endpoint = Mock()
            mock_exec_endpoint.post.side_effect = Exception("Command failed")
            return mock_exec_endpoint
        return Mock()
    
    mock_proxmox.nodes.return_value.qemu.return_value.agent.side_effect = agent_side_effect

    with pytest.raises(RuntimeError, match="Failed to execute command"):
        await vm_console.execute_command("node1", "100", "ls -l")

@pytest.mark.asyncio
async def test_execute_command_with_error_output(vm_console, mock_proxmox):
    """Test command execution with error output."""
    # Setup different mock return values for this test
    mock_status_endpoint = Mock()
    mock_status_endpoint.get.return_value = {
        "out-data": "",
        "err-data": "command error",
        "exitcode": 1,
        "exited": 1
    }
    
    def agent_side_effect(endpoint_name):
        if endpoint_name == "exec":
            mock_exec_endpoint = Mock()
            mock_exec_endpoint.post.return_value = {"pid": 12345}
            return mock_exec_endpoint
        elif endpoint_name == "exec-status":
            return mock_status_endpoint
        return Mock()
    
    mock_proxmox.nodes.return_value.qemu.return_value.agent.side_effect = agent_side_effect

    result = await vm_console.execute_command("node1", "100", "invalid-command")

    assert result["success"] is True  # Success refers to API call, not command
    assert result["output"] == ""
    assert result["error"] == "command error"
    assert result["exit_code"] == 1
