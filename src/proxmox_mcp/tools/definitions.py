"""
Tool descriptions for Proxmox MCP tools.
"""

# Node tool descriptions
GET_NODES_DESC = """List all nodes in the Proxmox cluster with their status, CPU, memory, and role information.

Example:
{"node": "pve1", "status": "online", "cpu_usage": 0.15, "memory": {"used": "8GB", "total": "32GB"}}"""

GET_NODE_STATUS_DESC = """Get detailed status information for a specific Proxmox node.

Parameters:
node* - Name/ID of node to query (e.g. 'pve1')

Example:
{"cpu": {"usage": 0.15}, "memory": {"used": "8GB", "total": "32GB"}}"""

# VM tool descriptions
GET_VMS_DESC = """List all virtual machines across the cluster with their status and resource usage.

Example:
{"vmid": "100", "name": "ubuntu", "status": "running", "cpu": 2, "memory": 4096}"""

EXECUTE_VM_COMMAND_DESC = """Execute commands in a VM via QEMU guest agent.

Parameters:
node* - Host node name (e.g. 'pve1')
vmid* - VM ID number (e.g. '100')
command* - Shell command to run (e.g. 'uname -a')

Example:
{"success": true, "output": "Linux vm1 5.4.0", "exit_code": 0}"""

# Container tool descriptions
GET_CONTAINERS_DESC = """List all LXC containers across the cluster with their status and configuration.

Example:
{"vmid": "200", "name": "nginx", "status": "running", "template": "ubuntu-20.04"}"""

EXECUTE_CONTAINER_COMMAND_DESC = """Execute commands in an LXC container via SSH + pct exec.

Uses SSH to connect to the Proxmox host and executes 'pct exec {vmid} -- {command}'.
This is the recommended approach since Proxmox REST API doesn't support container exec.

Requirements:
- SSH configuration must be provided in config (optional ssh section)
- Container must be running
- SSH access to Proxmox host required
- User must have pct command permissions

Parameters:
node* - Host node name (e.g. 'pve1')
vmid* - Container ID number (e.g. '200')
command* - Shell command to run (e.g. 'uname -a')

Example:
{"success": true, "output": "Linux container1 5.4.0", "exit_code": 0}"""

EXECUTE_HOST_COMMAND_DESC = """Execute commands directly on the Proxmox host via SSH.

Used for Proxmox management commands that run on the host itself, such as:
- pct stop {vmid} - Stop a container
- pct start {vmid} - Start a container  
- pct reboot {vmid} - Reboot a container
- pct list - List all containers
- qm stop {vmid} - Stop a VM
- qm start {vmid} - Start a VM

Requirements:
- SSH configuration must be provided in config
- SSH access to Proxmox host required
- User must have permissions for the commands

Parameters:
node* - Host node name (e.g. 'pve1', 'control')
command* - Command to run on host (e.g. 'pct stop 103')

Example:
{"success": true, "output": "stopping container...", "exit_code": 0}"""

# Storage tool descriptions
GET_STORAGE_DESC = """List storage pools across the cluster with their usage and configuration.

Example:
{"storage": "local-lvm", "type": "lvm", "used": "500GB", "total": "1TB"}"""

# Cluster tool descriptions
GET_CLUSTER_STATUS_DESC = """Get overall Proxmox cluster health and configuration status.

Example:
{"name": "proxmox", "quorum": "ok", "nodes": 3, "ha_status": "active"}"""
