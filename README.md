# 🚀 Proxmox Manager - Proxmox MCP Server


A Python-based Model Context Protocol (MCP) server for interacting with Proxmox hypervisors, providing a clean interface for managing nodes, VMs, and containers.

## ✨ Features

- 🤖 Full integration with Cline
- 🛠️ Built with the official MCP SDK
- 🔒 Secure token-based authentication with Proxmox
- 🖥️ Tools for managing nodes, VMs, and LXC containers
- 💻 VM and container console command execution
- 🔧 Host command execution via SSH
- 📝 Configurable logging system
- ✅ Type-safe implementation with Pydantic
- 🎨 Rich output formatting with customizable themes




## 📦 Installation

### Prerequisites
- UV package manager (recommended)
- Python 3.10 or higher
- Git
- Access to a Proxmox server with API token credentials

Before starting, ensure you have:
- [ ] Proxmox server hostname or IP
- [ ] Proxmox API token (see [API Token Setup](#proxmox-api-token-setup))
- [ ] UV installed (`pip install uv`)

### Quick Install

1. Clone and set up environment:
   ```bash
   # Clone repository
   git clone https://github.com/netixc/ProxmoxMCP.git
   cd ProxmoxMCP

   # Create and activate virtual environment
   uv venv
   source .venv/bin/activate  # Linux/macOS
   ```

2. Install dependencies:
   ```bash
   # Install with development dependencies
   uv pip install -e ".[dev]"
   ```

3. Create configuration:
   ```bash
   # Create config directory and copy template
   mkdir -p proxmox-config
   cp proxmox-config/config.example.json proxmox-config/config.json
   ```

4. Edit `proxmox-config/config.json`:
   ```json
   {
       "proxmox": {
           "host": "PROXMOX_HOST",        # Required: Your Proxmox server address
           "port": 8006,                  # Optional: Default is 8006
           "verify_ssl": false,           # Optional: Set false for self-signed certs
           "service": "PVE"               # Optional: Default is PVE
       },
       "auth": {
           "user": "USER@pve",            # Required: Your Proxmox username
           "token_name": "TOKEN_NAME",    # Required: API token ID
           "token_value": "TOKEN_VALUE"   # Required: API token value
       },
       "logging": {
           "level": "INFO",               # Optional: DEBUG for more detail
           "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
           "file": "proxmox_mcp.log"      # Optional: Log to file
       },
       "ssh": {                           # Optional: Required for container/host commands
           "username": "root",            # Optional: Default is "root"
           "port": 22,                    # Optional: Default is 22
           "key_file": "/path/to/ssh/key", # Optional: SSH private key path
           "password": "password",        # Optional: SSH password (not recommended)
           "timeout": 30                  # Optional: Connection timeout in seconds
       }
   }
   ```

### Verifying Installation

1. Check Python environment:
   ```bash
   python -c "import proxmox_mcp; print('Installation OK')"
   ```

2. Run the tests:
   ```bash
   pytest
   ```

3. Verify configuration:
   ```bash
   # Linux/macOS
   PROXMOX_MCP_CONFIG="proxmox-config/config.json" python -m proxmox_mcp.server
   ```

   You should see either:
   - A successful connection to your Proxmox server
   - Or a connection error (if Proxmox details are incorrect)

## ⚙️ Configuration

### Proxmox API Token Setup
1. Log into your Proxmox web interface
2. Navigate to Datacenter -> Permissions -> API Tokens
3. Create a new API token:
   - Select a user (e.g., root@pam)
   - Enter a token ID (e.g., "mcp-token")
   - Uncheck "Privilege Separation" if you want full access
   - Save and copy both the token ID and secret


### MCP Client Configuration

 Add to your MCP settings:
```json
{
  "mcpServers": {
    "proxmox": {
      "command": "/absolute/path/to/ProxmoxMCP/run-server.sh"
    }
  }
}
```



# 🔧 Available Tools

The server provides the following MCP tools for interacting with Proxmox:

### get_nodes
Lists all nodes in the Proxmox cluster.

- Parameters: None
- Example Response:
  ```
  🖥️ Proxmox Nodes

  🖥️ pve-compute-01
    • Status: ONLINE
    • Uptime: ⏳ 156d 12h
    • CPU Cores: 64
    • Memory: 186.5 GB / 512.0 GB (36.4%)

  🖥️ pve-compute-02
    • Status: ONLINE
    • Uptime: ⏳ 156d 11h
    • CPU Cores: 64
    • Memory: 201.3 GB / 512.0 GB (39.3%)
  ```

### get_node_status
Get detailed status of a specific node.

- Parameters:
  - `node` (string, required): Name of the node
- Example Response:
  ```
  🖥️ Node: pve-compute-01
    • Status: ONLINE
    • Uptime: ⏳ 156d 12h
    • CPU Usage: 42.3%
    • CPU Cores: 64 (AMD EPYC 7763)
    • Memory: 186.5 GB / 512.0 GB (36.4%)
    • Network: ⬆️ 12.8 GB/s ⬇️ 9.2 GB/s
    • Temperature: 38°C
  ```

### get_vms
List all VMs across the cluster.

- Parameters: None
- Example Response:
  ```
  🗃️ Virtual Machines

  🗃️ prod-db-master (ID: 100)
    • Status: RUNNING
    • Node: pve-compute-01
    • CPU Cores: 16
    • Memory: 92.3 GB / 128.0 GB (72.1%)

  🗃️ prod-web-01 (ID: 102)
    • Status: RUNNING
    • Node: pve-compute-01
    • CPU Cores: 8
    • Memory: 12.8 GB / 32.0 GB (40.0%)
  ```

### get_storage
List available storage.

- Parameters: None
- Example Response:
  ```
  💾 Storage Pools

  💾 ceph-prod
    • Status: ONLINE
    • Type: rbd
    • Usage: 12.8 TB / 20.0 TB (64.0%)
    • IOPS: ⬆️ 15.2k ⬇️ 12.8k

  💾 local-zfs
    • Status: ONLINE
    • Type: zfspool
    • Usage: 3.2 TB / 8.0 TB (40.0%)
    • IOPS: ⬆️ 42.8k ⬇️ 35.6k
  ```

### get_cluster_status
Get overall cluster status.

- Parameters: None
- Example Response:
  ```
  ⚙️ Proxmox Cluster

    • Name: enterprise-cloud
    • Status: HEALTHY
    • Quorum: OK
    • Nodes: 4 ONLINE
    • Version: 8.1.3
    • HA Status: ACTIVE
    • Resources:
      - Total CPU Cores: 192
      - Total Memory: 1536 GB
      - Total Storage: 70 TB
    • Workload:
      - Running VMs: 7
      - Total VMs: 8
      - Average CPU Usage: 38.6%
      - Average Memory Usage: 42.8%
  ```

### get_containers
List all LXC containers across the cluster.

- Parameters: None
- Example Response:
  ```
  📦 LXC Containers

  📦 prod-redis (ID: 200)
    • Status: RUNNING
    • Node: pve-compute-01
    • Template: ubuntu-22.04
    • CPU Cores: 4
    • Memory: 8.0 GB / 16.0 GB (50.0%)

  📦 dev-database (ID: 201)
    • Status: STOPPED
    • Node: pve-compute-02
    • Template: debian-12
    • CPU Cores: 2
    • Memory: 0.0 GB / 8.0 GB (0.0%)
  ```

### execute_vm_command
Execute a command in a VM's console using QEMU Guest Agent.

- Parameters:
  - `node` (string, required): Name of the node where VM is running
  - `vmid` (string, required): ID of the VM
  - `command` (string, required): Command to execute
- Example Response:
  ```
  🔧 Console Command Result
    • Status: SUCCESS
    • Command: systemctl status nginx
    • Node: pve-compute-01
    • VM: prod-web-01 (ID: 102)

  Output:
  ● nginx.service - A high performance web server and a reverse proxy server
     Loaded: loaded (/lib/systemd/system/nginx.service; enabled; vendor preset: enabled)
     Active: active (running) since Tue 2025-02-18 15:23:45 UTC; 2 months 3 days ago
  ```
- Requirements:
  - VM must be running
  - QEMU Guest Agent must be installed and running in the VM
  - Command execution permissions must be enabled in the Guest Agent
- Error Handling:
  - Returns error if VM is not running
  - Returns error if VM is not found
  - Returns error if command execution fails
  - Includes command output even if command returns non-zero exit code

### execute_container_command
Execute a command in an LXC container via SSH and pct exec.

- Parameters:
  - `node` (string, required): Name of the node where container is running
  - `vmid` (string, required): ID of the container
  - `command` (string, required): Command to execute
- Example Response:
  ```
  🔧 Container Command Result
    • Status: SUCCESS
    • Command: systemctl status redis
    • Node: pve-compute-01
    • Container: prod-redis (ID: 200)

  Output:
  ● redis-server.service - Advanced key-value store
     Loaded: loaded (/lib/systemd/system/redis-server.service; enabled)
     Active: active (running) since Mon 2025-01-15 10:23:45 UTC; 1 month ago
  ```
- Requirements:
  - Container must be running
  - SSH configuration must be provided in config
  - SSH access to the Proxmox host
- Error Handling:
  - Returns error if container is not running
  - Returns error if SSH connection fails
  - Returns error if container is not found
  - Includes command output even if command returns non-zero exit code

### execute_host_command
Execute a command directly on the Proxmox host via SSH.

- Parameters:
  - `node` (string, required): Name of the target node
  - `command` (string, required): Command to execute
- Example Response:
  ```
  🔧 Host Command Result
    • Status: SUCCESS
    • Command: pct list
    • Node: pve-compute-01

  Output:
  VMID       Status     Lock         Name
  200        running                 prod-redis
  201        stopped                 dev-database
  ```
- Use Cases:
  - Container management: `pct start 200`, `pct stop 200`, `pct reboot 200`
  - VM management: `qm start 100`, `qm stop 100`, `qm reboot 100`
  - System monitoring: `pvesh get /nodes/NODE/status`
- Requirements:
  - SSH configuration must be provided in config
  - SSH access to the Proxmox host
- Error Handling:
  - Returns error if SSH connection fails
  - Returns error if node is not found
  - Includes command output even if command returns non-zero exit code

## 👨‍💻 Development

After activating your virtual environment:

- Run tests: `pytest`
- Format code: `black .`
- Type checking: `mypy .`
- Lint: `ruff .`

## 📁 Project Structure

```
proxmox-mcp/
├── src/
│   └── proxmox_mcp/
│       ├── server.py          # Main MCP server implementation
│       ├── config/            # Configuration handling
│       ├── core/              # Core functionality (Proxmox API, logging)
│       ├── formatting/        # Output formatting and themes
│       ├── tools/             # Tool implementations
│       │   ├── console/       # VM/container console operations
│       │   ├── cluster.py     # Cluster management tools
│       │   ├── container.py   # LXC container tools
│       │   ├── node.py        # Node management tools
│       │   ├── storage.py     # Storage management tools
│       │   └── vm.py          # Virtual machine tools
│       └── utils/             # Utilities (auth, logging)
├── tests/                     # Test suite
├── proxmox-config/
│   └── config.example.json    # Configuration template
├── run-server.sh             # Server startup script
├── requirements*.in          # Dependency files
├── uv.lock                   # UV lock file
├── pyproject.toml            # Project metadata and dependencies
└── LICENSE                   # MIT License
```

## 📄 License

MIT License
