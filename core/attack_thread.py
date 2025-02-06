import traceback
import threading
import subprocess
from core.data_classes import *
from core.config import *
from custom_modules import *

class AttackThread(threading.Thread):
    running_count = 0
    finished_count = 0
    error_count = 0

    def __init__(self, target_info: TargetInfo, module: Module, port: int):
        """
        Initializes an attack thread for running a module against a specific target.

        :param target_info: Instance of TargetInfo managing the target's state.
        :param module: Instance of Module representing the attack module.
        :param port: Target port.
        :param protocol: Protocol (e.g., "http", "smb").
        :param hostname: The target hostname.
        """
        super().__init__()
        self.target_info = target_info
        self.module = module
        self.port = port or 0
        self.filename = module.output_file
        self.daemon = True
        self.output = None

    def return_callable_func(self, cmd):
        if cmd in globals().keys():
                func = globals()[cmd]
                if callable(func): 
                    return func
        raise NameError(f"{self.module.name}: Function {cmd} not found")

    def run(self):
        """Runs the attack process in the thread and updates TargetInfo."""
        try:
            Config.log_info(f"Started Module: {self.module.name}")
            AttackThread.running_count += 1
                
            func = self.return_callable_func(self.module.command)        
            if func:
                # Run command (callable function or external command)
                switches = self.format_switches()
                self.output = func(self.target_info, self.port, switches)
            else:
                self._run_external_command()

            Config.log_info(f"Finished {self.module.name}")

            # Mark module as completed in TargetInfo
            self.target_info.complete_module(self.port, self.module.name)
            AttackThread.finished_count += 1
            self._process_analysis()

        except Exception as e:
            Config.log_error(f"Exception in AttackThread ({self.module.name}): \n{traceback.format_exc()}")            
            AttackThread.error_count += 1
        finally:
            AttackThread.running_count -= 1            
            
    def format_switches(self):        
        port_data = self.target_info.get_port(self.port)
        return [ switch.replace("[protocol]", port_data.protocol if port_data else f"port_{self.port}_no_data")
                .replace("[hostname]", self.target_info.get_host())
                .replace("[port]", str(self.port))                
        for switch in self.module.switches]
        

    def _run_external_command(self):
        """Runs an external command and captures output to a file."""
        try:
            with open(self.filename, "w") as outfile:
                command = [self.command] + self.format_switches()
                subprocess.call(" ".join(command),stdout=outfile, stderr=outfile, shell=True)
        except Exception as e:
            Config.log_error(f"Failed to execute external command {self.module.command}: {e}")
            raise

    def _process_analysis(self):
        """Handles analysis of the output after execution."""
        func = self.return_callable_func(self.module.analyse_func)    
        if func:
            Config.log_info(f"Running analysis for Module: {self.module.name}")
            if not self.output and self.filename.exists():
                with open(self.filename, 'r') as file:
                    self.output = file.readlines()
            func(self.target_info, self.output)        
