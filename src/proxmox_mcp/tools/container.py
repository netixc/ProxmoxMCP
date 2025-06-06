"""
Container management tools for Proxmox LXC containers.

This module provides functionality for managing LXC containers in Proxmox:
- Listing containers across the cluster
- Getting container status and configuration
- Executing commands within containers via SSH + pct exec
- Managing container lifecycle

The ContainerTools class provides a comprehensive interface for container
operations, with proper error handling and status tracking.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from mcp.types import TextContent as Content
from .base import ProxmoxTool

if TYPE_CHECKING:
    from ..config.models import SSHConfig


class ContainerTools(ProxmoxTool):
    """Tools for managing Proxmox LXC containers.
    
    This class provides functionality for:
    - Listing all containers across the cluster
    - Getting detailed container information
    - Executing commands within running containers via SSH + pct exec
    - Monitoring container status and resource usage
    
    Uses the Proxmox API /nodes/{node}/lxc endpoints for container operations.
    For command execution, uses SSH to the Proxmox host with pct exec.
    Requires appropriate permissions for container management.
    """
    
    def __init__(self, proxmox_api_or_manager, ssh_config: Optional["SSHConfig"] = None):
        """Initialize the container tools.

        Args:
            proxmox_api_or_manager: Either a ProxmoxAPI instance or ProxmoxManager instance
            ssh_config: Optional SSH configuration for container command execution
        """
        super().__init__(proxmox_api_or_manager)
        self.ssh_config = ssh_config

    def get_containers(self) -> List[Content]:
        """List all LXC containers across the cluster with status and configuration.

        Retrieves comprehensive information for each container including:
        - Container ID and name
        - Current status (running, stopped, etc.)
        - Node assignment
        - Resource allocation (CPU, memory)
        - Template information
        - Network configuration

        Returns:
            List of Content objects containing formatted container information:
            [
                {
                    "vmid": "200",
                    "name": "webserver",
                    "status": "running",
                    "node": "pve1",
                    "template": "ubuntu-22.04",
                    "maxmem": 2147483648,
                    "cpus": 2
                }
            ]

        Raises:
            RuntimeError: If container list retrieval fails
        """
        try:
            # Get all nodes first
            nodes = self.proxmox.nodes.get()
            containers = []

            # Get containers from each node
            for node in nodes:
                node_name = node["node"]
                try:
                    # Get containers on this node
                    node_containers = self.proxmox.nodes(node_name).lxc.get()
                    
                    for container in node_containers:
                        container_id = container["vmid"]
                        
                        # Get detailed container info
                        try:
                            config = self.proxmox.nodes(node_name).lxc(container_id).config.get()
                            status = self.proxmox.nodes(node_name).lxc(container_id).status.current.get()
                            
                            containers.append({
                                "vmid": container_id,
                                "name": container.get("name", f"CT{container_id}"),
                                "status": container.get("status", "unknown"),
                                "node": node_name,
                                "template": config.get("ostemplate", "Unknown"),
                                "maxmem": container.get("maxmem", 0),
                                "mem": status.get("mem", 0),
                                "cpus": container.get("cpus", 0),
                                "maxcpu": status.get("cpus", container.get("cpus", 0)),
                                "disk": container.get("maxdisk", 0),
                                "netin": status.get("netin", 0),
                                "netout": status.get("netout", 0)
                            })
                        except Exception:
                            # Fallback to basic info if detailed status fails
                            containers.append({
                                "vmid": container_id,
                                "name": container.get("name", f"CT{container_id}"),
                                "status": container.get("status", "unknown"),
                                "node": node_name,
                                "template": "Unknown",
                                "maxmem": container.get("maxmem", 0),
                                "mem": 0,
                                "cpus": container.get("cpus", 0),
                                "maxcpu": 0,
                                "disk": container.get("maxdisk", 0),
                                "netin": 0,
                                "netout": 0
                            })
                            
                except Exception as e:
                    self.logger.warning(f"Cannot get containers from node {node_name}: {e}")
                    continue

            return self._format_response(containers, "containers")
        except Exception as e:
            self._handle_error("get containers", e)

    async def execute_command(self, node: str, vmid: str, command: str) -> List[Content]:
        """Execute a command in an LXC container via SSH + pct exec.

        This method uses SSH to connect to the Proxmox host and executes commands
        within LXC containers using the 'pct exec' command. This is the recommended
        approach since Proxmox does not provide a REST API endpoint for container
        command execution.

        Requirements:
        - SSH configuration must be provided during initialization
        - Container must be running
        - SSH access to the Proxmox host must be available
        - User must have permissions to execute pct commands

        Args:
            node: Host node name (e.g., 'pve1', 'proxmox-node2')
            vmid: Container ID number (e.g., '200', '201')
            command: Shell command to run (e.g., 'uname -a', 'systemctl status nginx')

        Returns:
            List of Content objects containing formatted command output

        Raises:
            ValueError: If SSH is not configured or container is not running
            RuntimeError: If SSH connection or command execution fails
        """
        # Check if SSH is configured
        if not self.ssh_config:
            self.logger.warning(f"SSH not configured for container command execution")
            error_result = {
                "success": False,
                "output": "",
                "error": (
                    f"SSH configuration is required for container command execution. "
                    f"Add SSH configuration to enable this functionality.\n\n"
                    f"Alternative: ssh root@{node} 'pct exec {vmid} -- {command}'"
                ),
                "exit_code": -1,
                "container": vmid,
                "node": node,
                "command": command
            }
            return self._format_response(error_result, "container_command")

        try:
            # Verify container exists and is running
            container_status = self.proxmox.nodes(node).lxc(vmid).status.current.get()
            if container_status["status"] != "running":
                self.logger.error(f"Container {vmid} is not running")
                raise ValueError(f"Container {vmid} on node {node} is not running")

            self.logger.info(f"Executing command in container {vmid} via SSH: {command}")
            
            # Execute command via SSH + pct exec
            result = await self._execute_ssh_command(node, vmid, command)
            return self._format_response(result, "container_command")

        except ValueError:
            # Re-raise ValueError for container not running
            raise
        except Exception as e:
            self.logger.error(f"Failed to execute command in container {vmid}: {str(e)}")
            error_result = {
                "success": False,
                "output": "",
                "error": str(e),
                "exit_code": -1,
                "container": vmid,
                "node": node,
                "command": command
            }
            return self._format_response(error_result, "container_command")

    async def _execute_ssh_command(self, node: str, vmid: str, command: str) -> Dict[str, Any]:
        """Execute pct exec command via SSH to Proxmox host.
        
        Args:
            node: Proxmox node hostname
            vmid: Container ID
            command: Command to execute in container
            
        Returns:
            Dictionary with execution results
        """
        import paramiko
        import socket
        
        # Get Proxmox host from node name or use the configured host
        # For now, we'll use the configured Proxmox host
        # In production, you might want to resolve node names to IP addresses
        proxmox_host = self._get_node_host(node)
        
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            # Build pct exec command
            pct_command = f"pct exec {vmid} -- {command}"
            
            # Connect via SSH
            connect_kwargs = {
                "hostname": proxmox_host,
                "username": self.ssh_config.username,
                "port": self.ssh_config.port,
                "timeout": self.ssh_config.timeout
            }
            
            if self.ssh_config.key_file:
                connect_kwargs["key_filename"] = self.ssh_config.key_file
            elif self.ssh_config.password:
                connect_kwargs["password"] = self.ssh_config.password
            else:
                # Try to use SSH agent or default keys
                pass
                
            ssh_client.connect(**connect_kwargs)
            
            # Execute the pct command
            stdin, stdout, stderr = ssh_client.exec_command(pct_command)
            
            # Get results
            exit_code = stdout.channel.recv_exit_status()
            output = stdout.read().decode('utf-8', errors='replace')
            error_output = stderr.read().decode('utf-8', errors='replace')
            
            self.logger.info(f"Command executed successfully in container {vmid} (exit code: {exit_code})")
            
            return {
                "success": exit_code == 0,
                "output": output,
                "error": error_output,
                "exit_code": exit_code,
                "container": vmid,
                "node": node,
                "command": command
            }
            
        except (paramiko.AuthenticationException, paramiko.SSHException, socket.error) as e:
            self.logger.error(f"SSH connection failed: {str(e)}")
            raise RuntimeError(f"SSH connection to {proxmox_host} failed: {str(e)}")
        finally:
            ssh_client.close()
    
    def _get_node_host(self, node: str) -> str:
        """Get the hostname/IP for a Proxmox node.
        
        For now, we use the main Proxmox host from configuration.
        In a multi-node setup, you might want to resolve node names
        to specific IP addresses.
        
        Args:
            node: Node name
            
        Returns:
            Host address for the node
        """
        # For now, assume all nodes are accessible via the main Proxmox host
        # This works for single-node setups and most cluster configurations
        if hasattr(self, '_proxmox_manager') and self._proxmox_manager:
            # Access the host from the proxmox manager config
            return self._proxmox_manager.config.get('host', node)
        
        # Fallback - try to use the node name as hostname
        return node

    async def execute_host_command(self, node: str, command: str) -> List[Content]:
        """Execute a command directly on the Proxmox host (not inside a container).

        This method is used for Proxmox management commands like:
        - pct stop {vmid}
        - pct start {vmid}
        - pct reboot {vmid}
        - pct list
        - qm stop {vmid}
        - etc.

        Args:
            node: Host node name (e.g., 'pve1', 'control')
            command: Command to run on the host (e.g., 'pct stop 103')

        Returns:
            List of Content objects containing formatted command output

        Raises:
            ValueError: If SSH is not configured
            RuntimeError: If SSH connection or command execution fails
        """
        # Check if SSH is configured
        if not self.ssh_config:
            self.logger.warning(f"SSH not configured for host command execution")
            error_result = {
                "success": False,
                "output": "",
                "error": (
                    f"SSH configuration is required for host command execution. "
                    f"Add SSH configuration to enable this functionality."
                ),
                "exit_code": -1,
                "node": node,
                "command": command
            }
            return self._format_response(error_result, "host_command")

        try:
            self.logger.info(f"Executing host command on {node}: {command}")
            
            # Execute command directly on host
            result = await self._execute_host_ssh_command(node, command)
            return self._format_response(result, "host_command")

        except Exception as e:
            self.logger.error(f"Failed to execute host command: {str(e)}")
            error_result = {
                "success": False,
                "output": "",
                "error": str(e),
                "exit_code": -1,
                "node": node,
                "command": command
            }
            return self._format_response(error_result, "host_command")

    async def _execute_host_ssh_command(self, node: str, command: str) -> Dict[str, Any]:
        """Execute command directly on Proxmox host via SSH.
        
        Args:
            node: Proxmox node hostname
            command: Command to execute on host
            
        Returns:
            Dictionary with execution results
        """
        import paramiko
        import socket
        
        proxmox_host = self._get_node_host(node)
        
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            # Connect via SSH
            connect_kwargs = {
                "hostname": proxmox_host,
                "username": self.ssh_config.username,
                "port": self.ssh_config.port,
                "timeout": self.ssh_config.timeout
            }
            
            if self.ssh_config.key_file:
                connect_kwargs["key_filename"] = self.ssh_config.key_file
            elif self.ssh_config.password:
                connect_kwargs["password"] = self.ssh_config.password
                
            ssh_client.connect(**connect_kwargs)
            
            # Execute the command directly on host
            stdin, stdout, stderr = ssh_client.exec_command(command)
            
            # Get results
            exit_code = stdout.channel.recv_exit_status()
            output = stdout.read().decode('utf-8', errors='replace')
            error_output = stderr.read().decode('utf-8', errors='replace')
            
            self.logger.info(f"Host command executed successfully (exit code: {exit_code})")
            
            return {
                "success": exit_code == 0,
                "output": output,
                "error": error_output,
                "exit_code": exit_code,
                "node": node,
                "command": command
            }
            
        except (paramiko.AuthenticationException, paramiko.SSHException, socket.error) as e:
            self.logger.error(f"SSH connection failed: {str(e)}")
            raise RuntimeError(f"SSH connection to {proxmox_host} failed: {str(e)}")
        finally:
            ssh_client.close()