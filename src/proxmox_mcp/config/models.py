"""
Configuration models for the Proxmox MCP server.

This module defines Pydantic models for configuration validation:
- Proxmox connection settings
- Authentication credentials
- Logging configuration
- Tool-specific parameter models

The models provide:
- Type validation
- Default values
- Field descriptions
- Required vs optional field handling
"""
from typing import Optional, Annotated
from pydantic import BaseModel, Field

class NodeStatus(BaseModel):
    """Model for node status query parameters.
    
    Validates and documents the required parameters for
    querying a specific node's status in the cluster.
    """
    node: Annotated[str, Field(description="Name/ID of node to query (e.g. 'pve1', 'proxmox-node2')")]

class VMCommand(BaseModel):
    """Model for VM command execution parameters.
    
    Validates and documents the required parameters for
    executing commands within a VM via QEMU guest agent.
    """
    node: Annotated[str, Field(description="Host node name (e.g. 'pve1', 'proxmox-node2')")]
    vmid: Annotated[str, Field(description="VM ID number (e.g. '100', '101')")]
    command: Annotated[str, Field(description="Shell command to run (e.g. 'uname -a', 'systemctl status nginx')")]

class ProxmoxConfig(BaseModel):
    """Model for Proxmox connection configuration.
    
    Defines the required and optional parameters for
    establishing a connection to the Proxmox API server.
    Provides sensible defaults for optional parameters.
    """
    host: str  # Required: Proxmox host address
    port: int = 8006  # Optional: API port (default: 8006)
    verify_ssl: bool = True  # Optional: SSL verification (default: True)
    service: str = "PVE"  # Optional: Service type (default: PVE)

class AuthConfig(BaseModel):
    """Model for Proxmox authentication configuration.
    
    Defines the required parameters for API authentication
    using token-based authentication. All fields are required
    to ensure secure API access.
    """
    user: str  # Required: Username (e.g., 'root@pam')
    token_name: str  # Required: API token name
    token_value: str  # Required: API token secret

class SSHConfig(BaseModel):
    """Model for SSH configuration for container command execution.
    
    Defines SSH connection parameters for executing commands
    in LXC containers via 'pct exec' on the Proxmox host.
    All fields are optional with sensible defaults.
    """
    username: str = "root"  # Optional: SSH username (default: root)
    port: int = 22  # Optional: SSH port (default: 22)
    key_file: Optional[str] = None  # Optional: SSH private key file path
    password: Optional[str] = None  # Optional: SSH password (not recommended)
    timeout: int = 30  # Optional: SSH connection timeout in seconds

class LoggingConfig(BaseModel):
    """Model for logging configuration.
    
    Defines logging parameters with sensible defaults.
    Supports both file and console logging with
    customizable format and log levels.
    """
    level: str = "INFO"  # Optional: Log level (default: INFO)
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"  # Optional: Log format
    file: Optional[str] = None  # Optional: Log file path (default: None for console logging)

class Config(BaseModel):
    """Root configuration model.
    
    Combines all configuration models into a single validated
    configuration object. Proxmox, auth, and logging sections are required.
    SSH configuration is optional for container command execution.
    """
    proxmox: ProxmoxConfig  # Required: Proxmox connection settings
    auth: AuthConfig  # Required: Authentication credentials
    logging: LoggingConfig  # Required: Logging configuration
    ssh: Optional[SSHConfig] = None  # Optional: SSH configuration for container commands
