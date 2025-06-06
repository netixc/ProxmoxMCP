#!/bin/bash
# Simple wrapper script for ProxmoxMCP server

cd "$(dirname "$0")"
source .venv/bin/activate
exec proxmox-mcp "$@"