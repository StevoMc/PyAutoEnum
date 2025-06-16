"""Core scanning functionality for PyAutoEnum."""

import threading
import time
import traceback

from pyautoenum.config.manager import ConfigManager
from pyautoenum.core.attack_thread import AttackThread
from pyautoenum.modules.custom import check_open_ports
from pyautoenum.utils.network import check_target_up


class ScanManager:
    """
    Manages the scanning process for a given target.
    """
    
    def __init__(self):
        """Initialize the scan manager."""
        self._stop_requested = False
        
    def start_scan(self):
        """
        Start scanning the target, storing results in the TargetInfo instance.
        """
        if not ConfigManager.target_info:
            ConfigManager.log_error("No target information available")
            return
            
        target = ConfigManager.target_info.get_host()
        if not target:
            ConfigManager.log_error("No valid target specified")
            return

        ConfigManager.log_info(f"Starting enumeration for {target}")

        # Check if target can be pinged
        if not check_target_up(target):
            ConfigManager.log_warning(f"Target {target} did NOT respond to ping")
        else:
            ConfigManager.log_success("Target is up")

        # If no open ports exist yet, perform an NMAP scan
        if not ConfigManager.target_info.ports:
            nmap_args = ["-Pn", "-F", "-T4"]
            ConfigManager.log_info(f"Started fast NMAP scan (nmap {target} {' '.join(nmap_args)})")
            nmap_results = check_open_ports(ConfigManager.target_info, None, nmap_args)
            if nmap_results:
                ConfigManager.target_info.merge(nmap_results)

        # Main scanning loop
        while not self._stop_requested:
            # Check modules that match requirements and start them
            self._check_and_start_modules()
            
            # Save current state
            if ConfigManager.target_info:
                ConfigManager.target_info.save_to_file()
            
            # Wait before next iteration
            time.sleep(3)
    
    def stop(self):
        """Request scan to stop."""
        self._stop_requested = True
    
    def _check_and_start_modules(self):
        """Check and start modules that match the current state."""
        if not ConfigManager.target_info:
            ConfigManager.log_error("No target information available")
            return
            
        for module in ConfigManager.modules:
            # Process port-specific modules
            if module.needs_port():
                for port, port_data in ConfigManager.target_info.ports.items():
                    # Check if module requirements are met and it hasn't been run already
                    if (module.meets_requirements(port_data) and 
                            not ConfigManager.target_info.check_module_finished(port, module.name)):
                        # Start attack thread for this module and port
                        ConfigManager.log_info(f"Starting module {module.name} for port {port}")
                        attack_thread = AttackThread(module, port)
                        attack_thread.start()
            else:
                # Handle target-wide modules (not port specific)
                # If the module has no port requirement and hasn't been run yet,
                # run it against the target as a whole
                if not ConfigManager.target_info.check_module_finished(None, module.name):
                    ConfigManager.log_info(f"Starting module {module.name} for target")
                    attack_thread = AttackThread(module, None)
                    attack_thread.start()


class ScanThread(threading.Thread):
    """
    Manages a scanning process in a separate thread using a ScanManager.
    """

    def __init__(self):
        """Initialize the scan thread."""
        super().__init__()
        self.scan_manager = ScanManager()
        self.finished = False
        self.daemon = True

    def run(self):
        """Execute the scan in a separate thread."""
        try:
            self.scan_manager.start_scan()
            self.finished = True
        except Exception:
            ConfigManager.log_error(f"Exception in ScanThread: {traceback.format_exc()}")
    
    def stop(self):
        """Stop the scan."""
        if self.scan_manager:
            self.scan_manager.stop()
