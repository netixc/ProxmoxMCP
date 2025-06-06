"""
Output templates for Proxmox MCP resource types.
"""
from typing import Dict, List, Any
from .formatters import ProxmoxFormatters
from .theme import ProxmoxTheme
from .colors import ProxmoxColors
from .components import ProxmoxComponents

class ProxmoxTemplates:
    """Output templates for different Proxmox resource types."""
    
    @staticmethod
    def node_list(nodes: List[Dict[str, Any]]) -> str:
        """Template for node list output.
        
        Args:
            nodes: List of node data dictionaries
            
        Returns:
            Formatted node list string
        """
        result = [f"{ProxmoxTheme.RESOURCES['node']} Proxmox Nodes"]
        
        for node in nodes:
            # Get node status
            status = node.get("status", "unknown")
            
            # Get memory info
            memory = node.get("memory", {})
            memory_used = memory.get("used", 0)
            memory_total = memory.get("total", 0)
            
            # Handle cases where memory values might be strings (permission errors)
            if isinstance(memory_used, str) or isinstance(memory_total, str):
                memory_display = f"{memory_used} / {memory_total}"
                memory_percent = 0
            else:
                memory_percent = (memory_used / memory_total * 100) if memory_total > 0 else 0
                memory_display = f"{ProxmoxFormatters.format_bytes(memory_used)} / {ProxmoxFormatters.format_bytes(memory_total)} ({memory_percent:.1f}%)"
            
            # Format node info
            result.extend([
                "",  # Empty line between nodes
                f"{ProxmoxTheme.RESOURCES['node']} {node['node']}",
                f"  • Status: {status.upper()}",
                f"  • Uptime: {ProxmoxFormatters.format_uptime(node.get('uptime', 0))}",
                f"  • CPU Cores: {node.get('maxcpu', 'N/A')}",
                f"  • Memory: {memory_display}"
            ])
            
            # Add disk usage if available
            disk = node.get("disk", {})
            if disk:
                disk_used = disk.get("used", 0)
                disk_total = disk.get("total", 0)
                disk_percent = (disk_used / disk_total * 100) if disk_total > 0 else 0
                result.append(
                    f"  • Disk: {ProxmoxFormatters.format_bytes(disk_used)} / "
                    f"{ProxmoxFormatters.format_bytes(disk_total)} ({disk_percent:.1f}%)"
                )
            
        return "\n".join(result)
    
    @staticmethod
    def node_status(node: str, status: Dict[str, Any]) -> str:
        """Template for detailed node status output.
        
        Args:
            node: Node name
            status: Node status data
            
        Returns:
            Formatted node status string
        """
        memory = status.get("memory", {})
        memory_used = memory.get("used", 0)
        memory_total = memory.get("total", 0)
        memory_percent = (memory_used / memory_total * 100) if memory_total > 0 else 0
        
        # Extract CPU information from cpuinfo
        cpuinfo = status.get("cpuinfo", {})
        cpu_cores = cpuinfo.get("cpus", "N/A")
        cpu_usage = status.get("cpu", 0) * 100  # Convert to percentage
        
        # Node is online if we can get its status
        node_status = "RUNNING" if status else "UNKNOWN"
        
        result = [
            f"{ProxmoxTheme.RESOURCES['node']} Node: {node}",
            f"  • Status: {node_status}",
            f"  • Uptime: {ProxmoxFormatters.format_uptime(status.get('uptime', 0))}",
            f"  • CPU Cores: {cpu_cores}",
            f"  • CPU Usage: {cpu_usage:.1f}%",
            f"  • Memory: {ProxmoxFormatters.format_bytes(memory_used)} / "
            f"{ProxmoxFormatters.format_bytes(memory_total)} ({memory_percent:.1f}%)"
        ]
        
        # Add root filesystem usage
        rootfs = status.get("rootfs", {})
        if rootfs:
            disk_used = rootfs.get("used", 0)
            disk_total = rootfs.get("total", 0)
            disk_percent = (disk_used / disk_total * 100) if disk_total > 0 else 0
            result.append(
                f"  • Root FS: {ProxmoxFormatters.format_bytes(disk_used)} / "
                f"{ProxmoxFormatters.format_bytes(disk_total)} ({disk_percent:.1f}%)"
            )
        
        # Add swap usage if available
        swap = status.get("swap", {})
        if swap and swap.get("total", 0) > 0:
            swap_used = swap.get("used", 0)
            swap_total = swap.get("total", 0)
            swap_percent = (swap_used / swap_total * 100) if swap_total > 0 else 0
            result.append(
                f"  • Swap: {ProxmoxFormatters.format_bytes(swap_used)} / "
                f"{ProxmoxFormatters.format_bytes(swap_total)} ({swap_percent:.1f}%)"
            )
        
        return "\n".join(result)
    
    @staticmethod
    def vm_list(vms: List[Dict[str, Any]]) -> str:
        """Template for VM list output.
        
        Args:
            vms: List of VM data dictionaries
            
        Returns:
            Formatted VM list string
        """
        result = [f"{ProxmoxTheme.RESOURCES['vm']} Virtual Machines"]
        
        for vm in vms:
            memory = vm.get("memory", {})
            memory_used = memory.get("used", 0)
            memory_total = memory.get("total", 0)
            memory_percent = (memory_used / memory_total * 100) if memory_total > 0 else 0
            
            result.extend([
                "",  # Empty line between VMs
                f"{ProxmoxTheme.RESOURCES['vm']} {vm['name']} (ID: {vm['vmid']})",
                f"  • Status: {vm['status'].upper()}",
                f"  • Node: {vm['node']}",
                f"  • CPU Cores: {vm.get('cpus', 'N/A')}",
                f"  • Memory: {ProxmoxFormatters.format_bytes(memory_used)} / "
                f"{ProxmoxFormatters.format_bytes(memory_total)} ({memory_percent:.1f}%)"
            ])
            
        return "\n".join(result)
    
    @staticmethod
    def storage_list(storage: List[Dict[str, Any]]) -> str:
        """Template for storage list output.
        
        Args:
            storage: List of storage data dictionaries
            
        Returns:
            Formatted storage list string
        """
        result = [f"{ProxmoxTheme.RESOURCES['storage']} Storage Pools"]
        
        for store in storage:
            used = store.get("used", 0)
            total = store.get("total", 0)
            percent = (used / total * 100) if total > 0 else 0
            
            result.extend([
                "",  # Empty line between storage pools
                f"{ProxmoxTheme.RESOURCES['storage']} {store['storage']}",
                f"  • Status: {store.get('status', 'unknown').upper()}",
                f"  • Type: {store['type']}",
                f"  • Usage: {ProxmoxFormatters.format_bytes(used)} / "
                f"{ProxmoxFormatters.format_bytes(total)} ({percent:.1f}%)"
            ])
            
        return "\n".join(result)
    
    @staticmethod
    def container_list(containers: List[Dict[str, Any]]) -> str:
        """Template for container list output.
        
        Args:
            containers: List of container data dictionaries
            
        Returns:
            Formatted container list string
        """
        if not containers:
            return f"{ProxmoxTheme.RESOURCES['container']} No containers found"
            
        result = [f"{ProxmoxTheme.RESOURCES['container']} Containers"]
        
        for container in containers:
            memory = container.get("memory", {})
            memory_used = memory.get("used", 0)
            memory_total = memory.get("total", 0)
            memory_percent = (memory_used / memory_total * 100) if memory_total > 0 else 0
            
            result.extend([
                "",  # Empty line between containers
                f"{ProxmoxTheme.RESOURCES['container']} {container['name']} (ID: {container['vmid']})",
                f"  • Status: {container['status'].upper()}",
                f"  • Node: {container['node']}",
                f"  • CPU Cores: {container.get('cpus', 'N/A')}",
                f"  • Memory: {ProxmoxFormatters.format_bytes(memory_used)} / "
                f"{ProxmoxFormatters.format_bytes(memory_total)} ({memory_percent:.1f}%)"
            ])
            
        return "\n".join(result)

    @staticmethod
    def cluster_status(status: Dict[str, Any]) -> str:
        """Template for cluster status output.
        
        Args:
            status: Cluster status data
            
        Returns:
            Formatted cluster status string
        """
        result = [f"{ProxmoxTheme.SECTIONS['configuration']} Proxmox Cluster"]
        
        # Basic cluster info
        result.extend([
            "",
            f"  • Name: {status.get('name', 'N/A')}",
            f"  • Quorum: {'OK' if status.get('quorum') else 'NOT OK'}",
            f"  • Nodes: {status.get('nodes', 0)}",
        ])
        
        # Add resource count if available
        resources = status.get('resources', [])
        if resources:
            result.append(f"  • Resources: {len(resources)}")
        
        return "\n".join(result)
    
    @staticmethod
    def container_list(containers: List[Dict[str, Any]]) -> str:
        """Template for container list output.
        
        Args:
            containers: List of container data dictionaries
            
        Returns:
            Formatted container list string
        """
        result = [f"{ProxmoxTheme.RESOURCES['container']} LXC Containers"]
        
        for container in containers:
            memory = container.get("mem", 0)
            max_memory = container.get("maxmem", 0)
            memory_percent = (memory / max_memory * 100) if max_memory > 0 else 0
            
            status = container.get("status", "unknown")
            
            result.extend([
                "",  # Empty line between containers
                f"{ProxmoxTheme.RESOURCES['container']} {container['name']} (ID: {container['vmid']})",
                f"  • Status: {status.upper()}",
                f"  • Node: {container.get('node', 'unknown')}",
                f"  • Template: {container.get('template', 'Unknown')}",
                f"  • CPU Cores: {container.get('cpus', 'N/A')}",
                f"  • Memory: {ProxmoxFormatters.format_bytes(memory)} / "
                f"{ProxmoxFormatters.format_bytes(max_memory)} ({memory_percent:.1f}%)"
            ])
            
            # Add disk usage if available
            disk = container.get("disk", 0)
            if disk > 0:
                result.append(f"  • Disk: {ProxmoxFormatters.format_bytes(disk)}")
                
        return "\n".join(result)
    
    @staticmethod
    def container_command(result: Dict[str, Any]) -> str:
        """Template for container command execution output.
        
        Args:
            result: Command execution result dictionary
            
        Returns:
            Formatted command output string
        """
        container_id = result.get("container", "unknown")
        node = result.get("node", "unknown") 
        command = result.get("command", "unknown")
        success = result.get("success", False)
        
        output_lines = [
            f"{ProxmoxTheme.SECTIONS['execution']} Container Command Execution",
            f"  • Container: {container_id} (Node: {node})",
            f"  • Command: {command}",
            f"  • Status: {'SUCCESS' if success else 'FAILED'}",
        ]
        
        if result.get("exit_code") is not None:
            output_lines.append(f"  • Exit Code: {result['exit_code']}")
        
        # Add output section
        output = result.get("output", "").strip()
        if output:
            output_lines.extend([
                "",
                f"{ProxmoxTheme.SECTIONS['output']} Output:",
                output
            ])
        
        # Add error section if there are errors
        error = result.get("error", "").strip()
        if error:
            output_lines.extend([
                "",
                f"{ProxmoxTheme.SECTIONS['error']} Error:",
                error
            ])
            
        return "\n".join(output_lines)
    
    @staticmethod
    def host_command(result: Dict[str, Any]) -> str:
        """Template for Proxmox host command execution output.
        
        Args:
            result: Command execution result dictionary
            
        Returns:
            Formatted command output string
        """
        node = result.get("node", "unknown") 
        command = result.get("command", "unknown")
        success = result.get("success", False)
        
        output_lines = [
            f"{ProxmoxTheme.SECTIONS['execution']} Proxmox Host Command Execution",
            f"  • Node: {node}",
            f"  • Command: {command}",
            f"  • Status: {'SUCCESS' if success else 'FAILED'}",
        ]
        
        if result.get("exit_code") is not None:
            output_lines.append(f"  • Exit Code: {result['exit_code']}")
        
        # Add output section
        output = result.get("output", "").strip()
        if output:
            output_lines.extend([
                "",
                f"{ProxmoxTheme.SECTIONS['output']} Output:",
                output
            ])
        
        # Add error section if there are errors
        error = result.get("error", "").strip()
        if error:
            output_lines.extend([
                "",
                f"{ProxmoxTheme.SECTIONS['error']} Error:",
                error
            ])
            
        return "\n".join(output_lines)
