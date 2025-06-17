"""Core scanning functionality for PyAutoEnum."""

import threading
import time
import traceback
from typing import Any, Dict

from pyautoenum.config.manager import ConfigManager
from pyautoenum.core.attack_thread import attack_thread_pool
from pyautoenum.data.models import PortData
from pyautoenum.modules.custom import check_open_ports
from pyautoenum.utils.network import check_target_up


class ScanManager:
    """
    Manages the scanning process for a given target.
    """
    
    def __init__(self):
        """Initialize the scan manager."""
        # 
        self._stop_requested = False
        self._discovery_complete = False
        self._target = ""
        self._scan_stats = {
            "modules_total": 0,
            "modules_completed": 0,
            "modules_running": 0,
            "discovery_status": "Not started",
            "elapsed_time": 0,
            "progress_percentage": 0,
            "target": "",
            "total_ports": 0,
        }
        self._start_time = 0
        # 
    
    @property
    def stats(self) -> Dict[str, Any]:
        """Get current scan statistics."""
        # 
        elapsed = time.time() - self._start_time if self._start_time else 0
        
        # Get thread pool stats
        # 
        pool_stats = attack_thread_pool.get_stats()
        
        
        # Update our stats
        self._scan_stats.update({
            "modules_completed": pool_stats["completed"],
            "modules_running": pool_stats["running"],
            "modules_total": pool_stats["total"],
            "elapsed_time": elapsed,
            "target": self._target,
            "total_ports": len(ConfigManager.target_info.ports) if ConfigManager.target_info else 0,
        })
        
        # Calculate progress percentage
        if self._scan_stats["modules_total"] > 0:
            self._scan_stats["progress_percentage"] = int(
                (self._scan_stats["modules_completed"] / self._scan_stats["modules_total"]) * 100
            )
        
        
        return self._scan_stats
        
    def start_scan(self):
        """
        Start scanning the target, storing results in the TargetInfo instance.
        """
        # 
        if not ConfigManager.target_info:
            # 
            ConfigManager.log_error("No target information available")
            return
            
        self._target = ConfigManager.target_info.get_host()
        
        self._start_time = time.time()
        self._scan_stats["target"] = self._target
        
        if not self._target:
            # 
            ConfigManager.log_error("No valid target specified")
            return

        
        ConfigManager.log_info(f"Starting enumeration for {self._target}")
        self._scan_stats["discovery_status"] = "Checking target availability"

        # Check if target can be pinged
        
        if not check_target_up(self._target):
            
            ConfigManager.log_warning(f"Target {self._target} did NOT respond to ping")
            self._scan_stats["discovery_status"] = "Target did not respond to ping, continuing anyway"
        else:
            # 
            ConfigManager.log_success("Target is up")
            self._scan_stats["discovery_status"] = "Target is up, performing port discovery"

        # If no open ports exist yet, perform an NMAP scan
        # 
        if not ConfigManager.target_info.ports:
            # 
            nmap_args = ["-Pn", "-F", "-T4"]
            ConfigManager.log_info(f"Started fast NMAP scan (nmap {self._target} {' '.join(nmap_args)})")
            
            nmap_results = check_open_ports(ConfigManager.target_info, None, nmap_args)
            
            if nmap_results:
                # 
                ConfigManager.target_info.merge(nmap_results)

        # Start the thread pool
        # 
        attack_thread_pool.start()
        # 
        self._scan_stats["discovery_status"] = "Port discovery complete, scanning services"
        self._discovery_complete = True
        # 

        # Main scanning loop
        while not self._stop_requested:
            # Check modules that match requirements and start them
            self._check_and_start_modules()
            
            # Save current state
            if ConfigManager.target_info:
                ConfigManager.target_info.save_to_file()
            
            # If stop requested, break out of the loop
            if self._stop_requested:
                # 
                break
                
            # Wait before next iteration
            time.sleep(1)
    
    def stop(self):
        """Request scan to stop."""
        # 
        self._stop_requested = True
        # 
        attack_thread_pool.stop()
        # 
    
    def _check_and_start_modules(self):
        """Check and start modules that match the current state."""
        if not ConfigManager.target_info:
            ConfigManager.log_error("No target information available")
            return
            
        tasks_added = False
        
        for module in ConfigManager.modules:
            # Process port-specific modules
            if module.needs_port():
                
                for port, port_data in ConfigManager.target_info.ports.items():
                    # Skip if module already run on this port
                    if module.name in port_data.modules:
                        
                        continue
                        
                    # Skip if protocol is required but not available
                    if module.protocol_list and not port_data.protocol:
                        
                        continue
                        
                    # Skip if port doesn't match protocol requirements
                    if module.protocol_list and port_data.protocol and port_data.protocol not in module.protocol_list:
                        
                        continue
                        
                    # Add task to thread pool
                    
                    attack_thread_pool.add_task(module, port)
                    tasks_added = True
            else:
                # Target-wide module (no specific port)
                
                
                # Ensure target port exists
                self._ensure_target_port_exists()
                
                # Skip if module already run on the target (stored in a special "target" port)
                if "target" in ConfigManager.target_info.ports and module.name in ConfigManager.target_info.ports["target"].modules:
                    
                    continue
                    
                # Check if this module should only run after port discovery
                if "discovery_complete" in module.requirements and not self._discovery_complete:
                    
                    continue
                    
                # Add task to thread pool
                
                attack_thread_pool.add_task(module)
                
                # Mark target-wide module as being run
                if "target" in ConfigManager.target_info.ports:
                    ConfigManager.target_info.ports["target"].modules.append(module.name)
                    
                    
                tasks_added = True
                    
        # Update progress stats with task info
        self._scan_stats["modules_total"] = attack_thread_pool.stats["total"]
        self._scan_stats["modules_completed"] = attack_thread_pool.stats["completed"]
        self._scan_stats["modules_pending"] = attack_thread_pool.stats["pending"]
        self._scan_stats["modules_running"] = attack_thread_pool.stats["running"]
        
        # Update progress percentage
        if self._scan_stats["modules_total"] > 0:
            self._scan_stats["progress_percentage"] = int(
                (self._scan_stats["modules_completed"] / self._scan_stats["modules_total"]) * 100
            )
            
        # If no new tasks were added and all tasks are complete, mark discovery complete
        if not tasks_added and attack_thread_pool.stats["running"] == 0 and attack_thread_pool.stats["pending"] == 0:
            if not self._stop_requested:
                # 
                if ConfigManager.ui_interface:
                    ConfigManager.ui_interface.set_status("Scan complete")
                
                # Save final results
                ConfigManager.target_info.save_to_file()
                
                # Mark scan as finished
                self._stop_requested = True
                # 

    def _ensure_target_port_exists(self):
        """Ensure the special 'target' port exists for tracking target-wide modules."""
        if not ConfigManager.target_info:
            # 
            return
            
        if "target" not in ConfigManager.target_info.ports:
            # 
            ConfigManager.target_info.ports["target"] = PortData()


class ScanThread(threading.Thread):
    """
    Manages a scanning process in a separate thread using a ScanManager.
    """

    def __init__(self):
        """Initialize the scan thread."""
        super().__init__()
        # 
        self.scan_manager = ScanManager()
        # 
        self.finished = False
        self.daemon = True
        # 
        
    @property
    def stats(self) -> Dict[str, Any]:
        """Get current scan statistics."""
        # 
        if self.scan_manager:
            stats = self.scan_manager.stats
            
            return stats
        # 
        return {}

    def run(self):
        """Execute the scan in a separate thread."""
        # 
        try:
            # 
            self.scan_manager.start_scan()
            # 
            self.finished = True
            # 
        except Exception as e:
            
            # 
            
            ConfigManager.log_error(f"Exception in ScanThread: {traceback.format_exc()}")
    
    def stop(self):
        """Stop the scan."""
        # 
        if self.scan_manager:
            # 
            self.scan_manager.stop()
            # 
