"""Attack thread implementation for PyAutoEnum."""

import subprocess
import threading
import traceback
from typing import List, Optional, Union

from pyautoenum.config.manager import ConfigManager


class AttackThread(threading.Thread):
    """Thread for running attack modules against a target."""
    
    # Class variables to track status
    running_count = 0
    finished_count = 0
    error_count = 0

    def __init__(self, module, port: Optional[Union[str, int]] = None):
        """
        Initialize an attack thread.
        
        Args:
            module: Module to run
            port: Target port or None for target-wide modules
        """
        super().__init__()
        self.module = module
        self.port = port
        self.daemon = True
        self.output = None

    def return_callable_func(self, cmd: str):
        """
        Get a callable function from module name.
        
        Args:
            cmd: Function name
            
        Returns:
            Callable function or None
        """
        # Try to find function in modules.custom
        from pyautoenum.modules import custom
        if hasattr(custom, cmd) and callable(getattr(custom, cmd)):
            return getattr(custom, cmd)
            
        return None

    def run(self):
        """Run the attack process in the thread and update TargetInfo."""
        try:
            ConfigManager.log_info(f"Started Module: {self.module.name}")
            AttackThread.running_count += 1

            # Ensure target_info is available before proceeding
            if not ConfigManager.target_info:
                ConfigManager.log_error("No target information available")
                return

            # Mark module as completed in TargetInfo
            ConfigManager.target_info.mark_module_as_run(self.port, self.module.name)

            # Check if the command is a Python function
            func = self.return_callable_func(self.module.command)
            if func:
                # Run Python function
                self.output = func(ConfigManager.target_info, self.port, self.module.switches)
            else:
                # Run external command
                self._run_external_command()

            ConfigManager.log_success(f"Finished Module: {self.module.name}")
            AttackThread.finished_count += 1
            
            # Run analysis if needed
            if self.module.analyse_func:
                self._process_analysis()

        except Exception:
            ConfigManager.log_error(
                f"Exception in AttackThread ({self.module.name}): \n{traceback.format_exc()}"
            )
            AttackThread.error_count += 1
        finally:
            AttackThread.running_count -= 1

    def format_switches(self) -> List[str]:
        """
        Format command-line switches with target-specific values.
        
        Returns:
            List of formatted command-line switches
        """
        if not ConfigManager.target_info:
            ConfigManager.log_error("No target information available")
            return []
            
        port_data = ConfigManager.target_info.get_port(self.port)
        hostname = ConfigManager.target_info.get_host()
        
        return [
            switch.replace(
                "[protocol]",
                port_data.protocol if port_data else f"port_{self.port}_no_data",
            )
            .replace("[hostname]", hostname)
            .replace("[port]", str(self.port) if self.port else "")
            .replace("[outfile]", self.module.output_file)
            for switch in self.module.switches
        ]

    def _run_external_command(self) -> None:
        """Run an external command and capture output to a file."""
        try:
            # Format command with arguments
            cmd = [self.module.command] + self.format_switches()
            cmd_str = " ".join(cmd)
            ConfigManager.log_info(f"Running command: {cmd_str}")
            
            # Execute command and capture output
            with open(self.module.output_file, "w") as outfile:
                process = subprocess.Popen(
                    cmd, 
                    stdout=outfile, 
                    stderr=subprocess.STDOUT,
                    text=True
                )
                process.wait()
                
            # Read output for analysis
            with open(self.module.output_file, "r") as f:
                self.output = f.read()
                
        except Exception as e:
            ConfigManager.log_error(f"Error running command {self.module.command}: {str(e)}")

    def _process_analysis(self) -> None:
        """Handle analysis of the output after execution."""
        analyse_func = self.return_callable_func(self.module.analyse_func)
        if analyse_func:
            try:
                if not ConfigManager.target_info:
                    ConfigManager.log_error("No target information available for analysis")
                    return
                    
                analyse_func(ConfigManager.target_info, self.output)
                ConfigManager.log_info(f"Analysis completed for {self.module.name}")
            except Exception as e:
                ConfigManager.log_error(f"Error in analysis for {self.module.name}: {str(e)}")
        else:
            ConfigManager.log_warning(f"Analysis function {self.module.analyse_func} not found for {self.module.name}")
