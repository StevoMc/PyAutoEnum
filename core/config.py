import threading
import os
import shutil
import yaml
from custom_modules import *
from core.data_classes import Module

class Config:
    # Static variables (directly accessible and mutable)
    path = ""
    display_data = []
    target_info = None
    modules = []

    # Static methods for logging
    logs = []
    logs_lock = threading.Lock()

    @classmethod
    def log_interaction(cls, text):
        cls._write_log(f"<{os.getlogin()}> " + str(text))

    @classmethod
    def log_error(cls, text):
        cls._write_log("[-] " + str(text))

    @classmethod
    def log_warning(cls, text):
        cls._write_log("[!] " + str(text))

    @classmethod
    def log_info(cls, text):
        cls._write_log("[*] " + str(text))

    @classmethod
    def log_success(cls, text):
        cls._write_log("[+] " + str(text))

    @classmethod
    def _write_log(cls, text):
        try:
            # Write the log to the file
            with cls.logs_lock:
                cls.logs.append(str(text))
                with open(cls.path / "logs.txt", "a") as file:
                    file.write(str(text) + "\n")

        except Exception as e:
            cls.log_error(f"Error writing log: {str(e)}")

    @classmethod
    def get_logs(cls):
        return cls.logs

    @classmethod
    def check_command_installed(cls, command):
            
            """Check if the given command is installed on the system."""
            if shutil.which(command):
                return True
            
            """Check if command is a callable function"""
            if command in globals().keys():
                func = globals()[command]
                if callable(func):
                    return True
            
            
            return False

    @classmethod
    def load_modules(cls, config_file):
        # Load file
        with open(config_file, "r", encoding="utf-8") as file:
            modules_data = yaml.safe_load(file)

        checked_modules = []
        failed_modules = []

        # Create Module instances
        for module_data in modules_data:
            # Extract module data
            name = module_data.get("name")
            description = module_data.get("description","")
            command = module_data.get("command","")
            switches = module_data.get("switches", [])
            analyse_func = module_data.get("analyse_function", None)
            protocols = module_data.get("protocols", [])

            # Check if the command is valid
            if Config.check_command_installed(command):
                # Instantiate the Module
                module = Module(name, description, command, protocol_list=protocols, switches=switches, analyse_func=analyse_func, config=cls)                                
                checked_modules.append(module)
            else:
                failed_modules.append(name)

        count_loaded = len(modules_data)
        count_errors = len(failed_modules)
        Config.log_success(f"Loaded {count_loaded - count_errors}/{count_loaded} Attack Modules")
        if failed_modules:
            Config.log_warning(f"Failed to load {len(failed_modules)} Attack Modules: [{','.join(failed_modules)}]")

        Config.modules = checked_modules