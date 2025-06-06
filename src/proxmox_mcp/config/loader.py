"""
Configuration loading utilities for the Proxmox MCP server.

This module handles loading and validation of server configuration:
- JSON configuration file loading
- Environment variable handling
- Configuration validation using Pydantic models
- Error handling for invalid configurations

The module ensures that all required configuration is present
and valid before the server starts operation.
"""
import json
import os
from typing import Optional
from .models import Config

def load_config(config_path: Optional[str] = None) -> Config:
    """Load and validate configuration from JSON file.

    Performs the following steps:
    1. Finds config file from environment variable or standard locations
    2. Loads JSON configuration file
    3. Validates required fields are present
    4. Converts to typed Config object using Pydantic
    
    Configuration must include:
    - Proxmox connection settings (host, port, etc.)
    - Authentication credentials (user, token)
    - Logging configuration
    
    Args:
        config_path: Path to the JSON configuration file
                    If not provided, searches standard locations

    Returns:
        Config object containing validated configuration:
        {
            "proxmox": {
                "host": "proxmox-host",
                "port": 8006,
                ...
            },
            "auth": {
                "user": "username",
                "token_name": "token-name",
                ...
            },
            "logging": {
                "level": "INFO",
                ...
            }
        }

    Raises:
        ValueError: If:
                 - Config file cannot be found
                 - JSON is invalid
                 - Required fields are missing
                 - Field values are invalid
    """
    if not config_path:
        # Try environment variable first
        config_path = os.environ.get("PROXMOX_MCP_CONFIG")
        
        # If not found, try standard locations
        if not config_path:
            # Get the directory where this package is installed
            package_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            # Look for config in standard locations
            possible_paths = [
                # Relative to package directory
                os.path.join(package_dir, "..", "proxmox-config", "config.json"),
                os.path.join(package_dir, "proxmox-config", "config.json"),
                # Current working directory
                "proxmox-config/config.json",
                "config.json",
                # Home directory
                os.path.expanduser("~/.proxmox-mcp/config.json"),
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    config_path = path
                    break
            
            if not config_path:
                raise ValueError(
                    "Config file not found. Please either:\n"
                    "1. Set PROXMOX_MCP_CONFIG environment variable, or\n"
                    "2. Place config.json in one of these locations:\n"
                    + "\n".join(f"   - {path}" for path in possible_paths)
                )

    try:
        with open(config_path) as f:
            config_data = json.load(f)
            if not config_data.get('proxmox', {}).get('host'):
                raise ValueError("Proxmox host cannot be empty")
            return Config(**config_data)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in config file: {e}")
    except Exception as e:
        raise ValueError(f"Failed to load config: {e}")
