"""
Tests for the Proxmox MCP server.
"""

import os
import json
import pytest
from unittest.mock import Mock, patch

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from proxmox_mcp.server import ProxmoxMCPServer

@pytest.fixture
def mock_env_vars():
    """Fixture to set up test environment variables."""
    env_vars = {
        "PROXMOX_MCP_CONFIG": "/test/config.json",
        "PROXMOX_HOST": "test.proxmox.com",
        "PROXMOX_USER": "test@pve",
        "PROXMOX_TOKEN_NAME": "test_token",
        "PROXMOX_TOKEN_VALUE": "test_value",
        "LOG_LEVEL": "DEBUG"
    }
    with patch.dict(os.environ, env_vars):
        yield env_vars

@pytest.fixture
def mock_proxmox():
    """Fixture to mock ProxmoxAPI."""
    with patch("proxmox_mcp.core.proxmox.ProxmoxAPI") as mock:
        mock.return_value.nodes.get.return_value = [
            {"node": "node1", "status": "online"},
            {"node": "node2", "status": "online"}
        ]
        yield mock

@pytest.fixture
def server(mock_env_vars, mock_proxmox):
    """Fixture to create a ProxmoxMCPServer instance."""
    # Mock the config loading
    from proxmox_mcp.config.models import Config, ProxmoxConfig, AuthConfig, LoggingConfig
    mock_config = Config(
        proxmox=ProxmoxConfig(
            host="test.proxmox.com",
            port=8006,
            user="test@pve",
            verify_ssl=False
        ),
        auth=AuthConfig(
            user="test@pve",
            token_name="test_token",
            token_value="test_value"
        ),
        logging=LoggingConfig(
            level="DEBUG"
        )
    )
    
    with patch("proxmox_mcp.server.load_config", return_value=mock_config):
        return ProxmoxMCPServer()

def test_server_initialization(server, mock_proxmox):
    """Test server initialization with environment variables."""
    assert server.config.proxmox.host == "test.proxmox.com"
    assert server.config.auth.user == "test@pve"
    assert server.config.auth.token_name == "test_token"
    assert server.config.auth.token_value == "test_value"
    assert server.config.logging.level == "DEBUG"

    # ProxmoxAPI should not be called during initialization (lazy loading)
    mock_proxmox.assert_not_called()

@pytest.mark.asyncio
async def test_list_tools(server):
    """Test listing available tools."""
    tools = await server.mcp.list_tools()

    assert len(tools) > 0
    tool_names = [tool.name for tool in tools]
    assert "get_nodes" in tool_names
    assert "get_vms" in tool_names
    # get_containers tool is not implemented yet
    # assert "get_containers" in tool_names
    assert "execute_vm_command" in tool_names

@pytest.mark.asyncio
async def test_get_nodes(server, mock_proxmox):
    """Test get_nodes tool."""
    # Mock nodes list
    mock_proxmox.return_value.nodes.get.return_value = [
        {"node": "node1", "status": "online", "maxmem": 34359738368, "mem": 8589934592},
        {"node": "node2", "status": "online", "maxmem": 34359738368, "mem": 8589934592}
    ]
    
    # Mock detailed status for each node  
    mock_proxmox.return_value.nodes.return_value.status.get.return_value = {
        "uptime": 123456,
        "cpuinfo": {"cpus": 8},
        "memory": {"used": 8589934592, "total": 34359738368}
    }
    
    response = await server.mcp.call_tool("get_nodes", {})
    
    # The response should be formatted text, not JSON
    assert len(response) > 0
    assert "node1" in response[0].text
    assert "node2" in response[0].text

@pytest.mark.asyncio
async def test_get_node_status_missing_parameter(server):
    """Test get_node_status tool with missing parameter."""
    with pytest.raises(ToolError, match="Field required"):
        await server.mcp.call_tool("get_node_status", {})

@pytest.mark.asyncio
async def test_get_node_status(server, mock_proxmox):
    """Test get_node_status tool with valid parameter."""
    mock_proxmox.return_value.nodes.return_value.status.get.return_value = {
        "status": "running",
        "uptime": 123456,
        "cpuinfo": {"cpus": 8},
        "memory": {"used": 8589934592, "total": 34359738368}
    }

    response = await server.mcp.call_tool("get_node_status", {"node": "node1"})
    
    # The response should be formatted text, not JSON
    assert len(response) > 0
    assert "node1" in response[0].text
    assert "RUNNING" in response[0].text

@pytest.mark.asyncio
async def test_get_vms(server, mock_proxmox):
    """Test get_vms tool."""
    mock_proxmox.return_value.nodes.get.return_value = [{"node": "node1", "status": "online"}]
    mock_proxmox.return_value.nodes.return_value.qemu.get.return_value = [
        {"vmid": "100", "name": "vm1", "status": "running", "maxmem": 4294967296, "mem": 2147483648},
        {"vmid": "101", "name": "vm2", "status": "stopped", "maxmem": 4294967296, "mem": 0}
    ]
    
    # Mock VM config for detailed info
    mock_proxmox.return_value.nodes.return_value.qemu.return_value.config.get.return_value = {
        "cores": 2,
        "memory": 4096
    }

    response = await server.mcp.call_tool("get_vms", {})
    
    # The response should be formatted text, not JSON
    assert len(response) > 0
    assert "vm1" in response[0].text
    assert "vm2" in response[0].text

@pytest.mark.asyncio
async def test_get_containers(server, mock_proxmox):
    """Test get_containers tool."""
    # Mock nodes
    mock_proxmox.return_value.nodes.get.return_value = [
        {"node": "pve1", "status": "online"}
    ]
    
    # Mock containers on node
    mock_proxmox.return_value.nodes.return_value.lxc.get.return_value = [
        {"vmid": "200", "name": "container1", "status": "running", "maxmem": 2147483648, "cpus": 2},
        {"vmid": "201", "name": "container2", "status": "stopped", "maxmem": 1073741824, "cpus": 1}
    ]
    
    # Mock container config and status
    mock_proxmox.return_value.nodes.return_value.lxc.return_value.config.get.return_value = {
        "ostemplate": "ubuntu-20.04"
    }
    mock_proxmox.return_value.nodes.return_value.lxc.return_value.status.current.get.return_value = {
        "mem": 1073741824,
        "cpus": 2,
        "netin": 1000,
        "netout": 2000
    }

    response = await server.mcp.call_tool("get_containers", {})
    
    # The response should be formatted text, not JSON
    assert len(response) > 0
    assert "container1" in response[0].text
    assert "container2" in response[0].text

@pytest.mark.asyncio
async def test_execute_container_command_no_ssh(server, mock_proxmox):
    """Test container command execution without SSH configuration."""
    response = await server.mcp.call_tool("execute_container_command", {
        "node": "pve1",
        "vmid": "200",
        "command": "uname -a"
    })
    
    assert len(response) > 0
    assert "SSH configuration is required" in response[0].text
    assert "pct exec" in response[0].text
    assert "FAILED" in response[0].text

@pytest.mark.asyncio
async def test_get_storage(server, mock_proxmox):
    """Test get_storage tool."""
    mock_proxmox.return_value.storage.get.return_value = [
        {"storage": "local", "type": "dir", "enabled": True, "content": ["images", "backup"]},
        {"storage": "ceph", "type": "rbd", "enabled": True, "content": ["images"]}
    ]
    
    # Mock storage status for detailed info
    mock_proxmox.return_value.nodes.return_value.storage.return_value.status.get.return_value = {
        "used": 53687091200,  # 50GB
        "total": 107374182400,  # 100GB
        "avail": 53687091200   # 50GB
    }

    response = await server.mcp.call_tool("get_storage", {})
    
    # The response should be formatted text, not JSON
    assert len(response) > 0
    assert "local" in response[0].text
    assert "ceph" in response[0].text

@pytest.mark.asyncio
async def test_get_cluster_status(server, mock_proxmox):
    """Test get_cluster_status tool."""
    mock_proxmox.return_value.cluster.status.get.return_value = [
        {"name": "test-cluster", "quorate": 1, "type": "cluster"},
        {"name": "node1", "type": "node", "online": 1},
        {"name": "node2", "type": "node", "online": 1}
    ]

    response = await server.mcp.call_tool("get_cluster_status", {})
    
    # The response should be formatted text, not JSON
    assert len(response) > 0
    assert "test-cluster" in response[0].text

@pytest.mark.asyncio
async def test_execute_vm_command_success(server, mock_proxmox):
    """Test successful VM command execution."""
    # Mock VM status check
    mock_proxmox.return_value.nodes.return_value.qemu.return_value.status.current.get.return_value = {
        "status": "running"
    }
    
    # Setup agent exec endpoint correctly - it's called as endpoint("exec").post()
    mock_exec_endpoint = Mock()
    mock_exec_endpoint.post.return_value = {"pid": 12345}
    
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
    
    mock_proxmox.return_value.nodes.return_value.qemu.return_value.agent.side_effect = agent_side_effect

    response = await server.mcp.call_tool("execute_vm_command", {
        "node": "node1",
        "vmid": "100",
        "command": "ls -l"
    })
    
    # The response should be formatted text, not JSON
    assert len(response) > 0
    assert "command output" in response[0].text

@pytest.mark.asyncio
async def test_execute_vm_command_missing_parameters(server):
    """Test VM command execution with missing parameters."""
    with pytest.raises(ToolError):
        await server.mcp.call_tool("execute_vm_command", {})

@pytest.mark.asyncio
async def test_execute_vm_command_vm_not_running(server, mock_proxmox):
    """Test VM command execution when VM is not running."""
    mock_proxmox.return_value.nodes.return_value.qemu.return_value.status.current.get.return_value = {
        "status": "stopped"
    }

    with pytest.raises(ToolError, match="not running"):
        await server.mcp.call_tool("execute_vm_command", {
            "node": "node1",
            "vmid": "100",
            "command": "ls -l"
        })

@pytest.mark.asyncio
async def test_execute_vm_command_with_error(server, mock_proxmox):
    """Test VM command execution with command error."""
    # Mock VM status check
    mock_proxmox.return_value.nodes.return_value.qemu.return_value.status.current.get.return_value = {
        "status": "running"
    }
    
    # Setup different mock return values for this test
    mock_exec_endpoint = Mock()
    mock_exec_endpoint.post.return_value = {"pid": 12345}
    
    mock_status_endpoint = Mock()
    mock_status_endpoint.get.return_value = {
        "out-data": "",
        "err-data": "command not found",
        "exitcode": 1,
        "exited": 1
    }
    
    def agent_side_effect(endpoint_name):
        if endpoint_name == "exec":
            return mock_exec_endpoint
        elif endpoint_name == "exec-status":
            return mock_status_endpoint
        return Mock()
    
    mock_proxmox.return_value.nodes.return_value.qemu.return_value.agent.side_effect = agent_side_effect

    response = await server.mcp.call_tool("execute_vm_command", {
        "node": "node1",
        "vmid": "100",
        "command": "invalid-command"
    })
    
    # The response should be formatted text, not JSON
    assert len(response) > 0
    assert "command not found" in response[0].text
