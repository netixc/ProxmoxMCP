"""
Main server implementation for Proxmox MCP.

This module implements the core MCP server for Proxmox integration, providing:
- Configuration loading and validation
- Logging setup
- Proxmox API connection management
- MCP tool registration and routing
- Signal handling for graceful shutdown

The server exposes a set of tools for managing Proxmox resources including:
- Node management
- VM operations
- Storage management
- Cluster status monitoring
"""
import logging
import os
import sys
import signal
from typing import Optional, List, Annotated

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.tools import Tool
from mcp.types import TextContent as Content
from pydantic import Field

from .config.loader import load_config
from .core.logging import setup_logging
from .core.proxmox import ProxmoxManager
from .tools.node import NodeTools
from .tools.vm import VMTools
from .tools.storage import StorageTools
from .tools.cluster import ClusterTools
from .tools.container import ContainerTools
from .tools.definitions import (
    GET_NODES_DESC,
    GET_NODE_STATUS_DESC,
    GET_VMS_DESC,
    EXECUTE_VM_COMMAND_DESC,
    GET_CONTAINERS_DESC,
    EXECUTE_CONTAINER_COMMAND_DESC,
    EXECUTE_HOST_COMMAND_DESC,
    GET_STORAGE_DESC,
    GET_CLUSTER_STATUS_DESC
)

class ProxmoxMCPServer:
    """Main server class for Proxmox MCP."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the server.

        Args:
            config_path: Path to configuration file
        """
        self.config = load_config(config_path)
        self.logger = setup_logging(self.config.logging)
        
        # Initialize core components  
        self.proxmox_manager = ProxmoxManager(self.config.proxmox, self.config.auth)
        
        # Initialize tools with manager (they will get API connection when first used)
        self.node_tools = NodeTools(self.proxmox_manager)
        self.vm_tools = VMTools(self.proxmox_manager)
        self.storage_tools = StorageTools(self.proxmox_manager)
        self.cluster_tools = ClusterTools(self.proxmox_manager)
        self.container_tools = ContainerTools(self.proxmox_manager, self.config.ssh)
        
        # Initialize MCP server
        self.mcp = FastMCP("ProxmoxMCP")
        self._setup_tools()

    def _setup_tools(self) -> None:
        """Register MCP tools with the server.
        
        Initializes and registers all available tools with the MCP server:
        - Node management tools (list nodes, get status)
        - VM operation tools (list VMs, execute commands)
        - Container management tools (list containers, execute commands)
        - Storage management tools (list storage)
        - Cluster tools (get cluster status)
        
        Each tool is registered with appropriate descriptions and parameter
        validation using Pydantic models.
        """
        
        # Node tools
        @self.mcp.tool(description=GET_NODES_DESC)
        def get_nodes():
            return self.node_tools.get_nodes()

        @self.mcp.tool(description=GET_NODE_STATUS_DESC)
        def get_node_status(
            node: Annotated[str, Field(description="Name/ID of node to query (e.g. 'pve1', 'proxmox-node2')")]
        ):
            return self.node_tools.get_node_status(node)

        # VM tools
        @self.mcp.tool(description=GET_VMS_DESC)
        def get_vms():
            return self.vm_tools.get_vms()

        @self.mcp.tool(description=EXECUTE_VM_COMMAND_DESC)
        async def execute_vm_command(
            node: Annotated[str, Field(description="Host node name (e.g. 'pve1', 'proxmox-node2')")],
            vmid: Annotated[str, Field(description="VM ID number (e.g. '100', '101')")],
            command: Annotated[str, Field(description="Shell command to run (e.g. 'uname -a', 'systemctl status nginx')")]
        ):
            return await self.vm_tools.execute_command(node, vmid, command)

        # Container tools
        @self.mcp.tool(description=GET_CONTAINERS_DESC)
        def get_containers():
            return self.container_tools.get_containers()

        @self.mcp.tool(description=EXECUTE_CONTAINER_COMMAND_DESC)
        async def execute_container_command(
            node: Annotated[str, Field(description="Host node name (e.g. 'pve1', 'proxmox-node2')")],
            vmid: Annotated[str, Field(description="Container ID number (e.g. '200', '201')")],
            command: Annotated[str, Field(description="Shell command to run (e.g. 'uname -a', 'systemctl status nginx')")]
        ):
            return await self.container_tools.execute_command(node, vmid, command)

        @self.mcp.tool(description=EXECUTE_HOST_COMMAND_DESC)
        async def execute_host_command(
            node: Annotated[str, Field(description="Host node name (e.g. 'pve1', 'control')")],
            command: Annotated[str, Field(description="Command to run on host (e.g. 'pct stop 103', 'pct list')")]
        ):
            return await self.container_tools.execute_host_command(node, command)

        # Storage tools
        @self.mcp.tool(description=GET_STORAGE_DESC)
        def get_storage():
            return self.storage_tools.get_storage()

        # Cluster tools
        @self.mcp.tool(description=GET_CLUSTER_STATUS_DESC)
        def get_cluster_status():
            return self.cluster_tools.get_cluster_status()

    async def run(self):
        """Run the MCP server."""
        await self.mcp.run_stdio_async()

def main():
    """Main entry point for the Proxmox MCP server."""
    import anyio
    
    async def run_server():
        try:
            server = ProxmoxMCPServer()
            await server.run()
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    
    try:
        anyio.run(run_server)
    except KeyboardInterrupt:
        sys.exit(0)

if __name__ == "__main__":
    main()
