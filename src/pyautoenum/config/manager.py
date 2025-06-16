"""Configuration management for PyAutoEnum."""

import os
import shutil
import threading
import traceback
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from pyautoenum.data.models import Module


class ConfigManager:
    """
    Manages configuration and state for the application.
    
    This class is designed as a singleton to provide global access
    to configuration data and application state.
    """
    
    # Static variables
    _instance = None
    path: str = ""
    display_data: List[str] = []
    target_info = None
    modules: List[Module] = []
    
    # Logging related
    logs: List[str] = []
    logs_lock = threading.Lock()
    
    def __new__(cls):
        """Ensure singleton pattern."""
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize config manager if not already initialized."""
        if self._initialized:
            return
            
        self._initialized = True
    
    def init_config(self, path: Optional[str] = None) -> None:
        """
        Initialize configuration with path for outputs.
        
        Args:
            path: Directory path for output files, or None for default
        """
        if path:
            self.path = path
        else:
            # Default to current directory
            self.path = str(Path.cwd() / "output")
            
        # Create output directory if it doesn't exist
        os.makedirs(self.path, exist_ok=True)
        
        self.log_info(f"Output path set to: {self.path}")
    
    def set_target_info(self, target_info) -> None:
        """
        Set the target information object.
        
        Args:
            target_info: The TargetInfo object
        """
        ConfigManager.target_info = target_info
    
    def load_modules(self, config_file: str | None = None) -> None:
        """
        Load attack modules from configuration file.
        
        Args:
            config_file: Path to modules configuration file, or None for default
        """
        if not config_file:
            # Check both potential locations for modules.yml
            if os.path.exists("modules.yml"):
                config_file = "modules.yml"
            elif os.path.exists(os.path.join("resources", "modules.yml")):
                config_file = os.path.join("resources", "modules.yml")
            else:
                resource_path = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)), 
                    "..", "resources", "modules.yml"
                )
                if os.path.exists(resource_path):
                    config_file = resource_path
                else:
                    self.log_error("Could not find modules.yml configuration file")
                    return
        
        try:
            # Load modules
            with open(config_file, "r", encoding="utf-8") as file:
                modules_data = yaml.safe_load(file)
            
            checked_modules = []
            failed_modules = []
            
            # Create Module instances
            for module_data in modules_data:
                # Extract module data
                name = module_data.get("name")
                description = module_data.get("description", "")
                command = module_data.get("command", "")
                switches = module_data.get("switches", [])
                analyse_func = module_data.get("analyse_function", "")
                
                protocols = module_data.get("protocols", [])
                protocols = [p.lower() for p in protocols]
                
                requirements = module_data.get("requires", [])
                requirements = [r.lower() for r in requirements]
                
                # Check if the command is valid
                if self.check_command_installed(command):
                    module = Module(
                        name=name,
                        description=description,
                        command=command,
                        requirements=requirements,
                        protocol_list=protocols,
                        switches=switches,
                        analyse_func=analyse_func,
                        config=self,
                    )
                    checked_modules.append(module)
                else:
                    failed_modules.append(f"{name} ({command})")
            
            count_loaded = len(modules_data)
            count_errors = len(failed_modules)
            self.log_success(f"Loaded {count_loaded - count_errors}/{count_loaded} Attack Modules")
            
            if failed_modules:
                self.log_warning(f"Failed to load modules: {', '.join(failed_modules)}")
            
            ConfigManager.modules = checked_modules
            
        except Exception as e:
            self.log_error(f"Error loading modules: {str(e)}")
    
    @classmethod
    def check_command_installed(cls, command: str) -> bool:
        """
        Check if the given command is installed on the system or available as a function.
        
        Args:
            command: Command name or function name to check
            
        Returns:
            Boolean indicating if command is available
        """
        # Check for system command
        if shutil.which(command):
            return True
        
        # Check for Python function
        from pyautoenum.modules import custom
        if hasattr(custom, command) and callable(getattr(custom, command)):
            return True
            
        return False
    
    # Logging methods
    @classmethod
    def log_interaction(cls, text: str) -> None:
        """Log user interaction."""
        cls._write_log(f"<{os.getlogin()}> {str(text)}")
    
    @classmethod
    def log_error(cls, text: str) -> None:
        """Log error message."""
        cls._write_log("[-] " + str(text))
    
    @classmethod
    def log_warning(cls, text: str) -> None:
        """Log warning message."""
        cls._write_log("[!] " + str(text))
    
    @classmethod
    def log_info(cls, text: str) -> None:
        """Log informational message."""
        cls._write_log("[*] " + str(text))
    
    @classmethod
    def log_success(cls, text: str) -> None:
        """Log success message."""
        cls._write_log("[+] " + str(text))
    
    @classmethod
    def _write_log(cls, text: str) -> None:
        """Write message to logs."""
        try:
            with cls.logs_lock:
                cls.logs.append(text)
                
                # Write to log file if path is set
                if cls.path:
                    log_file = os.path.join(cls.path, "logs.txt")
                    with open(log_file, "a") as f:
                        f.write(text + "\n")
                        
        except Exception as e:
            print(f"Error writing log: {str(e)}")
    
    @classmethod
    def get_logs(cls) -> List[str]:
        """Get all logged messages."""
        return cls.logs
