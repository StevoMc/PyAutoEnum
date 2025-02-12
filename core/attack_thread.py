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

    def __init__(self, module: Module, port=None):
        """
        Initializes an attack thread for running a module against a specific target.

        :param target_info: Instance of TargetInfo managing the target's state.
        :param module: Instance of Module representing the attack module.
        :param port: Target port.
        :param protocol: Protocol (e.g., "http", "smb").
        :param hostname: The target hostname.
        """
        super().__init__()        
        self.module = module
        self.port = port        
        self.daemon = True
        self.output = None

    def return_callable_func(self, cmd):
        if cmd in globals().keys():
                func = globals()[cmd]
                if callable(func): 
                    return func        

    def run(self):
        """Runs the attack process in the thread and updates TargetInfo."""
        try:
            Config.log_info(f"Started Module: {self.module.name}")
            AttackThread.running_count += 1
            
            # Mark module as completed in TargetInfo
            Config.target_info.mark_module_as_run(self.port, self.module.name)
                
            func = self.return_callable_func(self.module.command)        
            if func:
                # Run command (callable function or external command)
                switches = self.format_switches()                
                self.output = func(Config.target_info, self.port, switches)
                
                # only write when some output
                if self.output:                    
                    # only write result if result file is not created by command switches
                    if not os.path.exists(self.module.output_file):
                        with open(self.module.output_file, "w") as outfile:                            
                            str_ouput = str(self.output)
                            if isinstance(str_ouput, str):
                                outfile.write(str_ouput)
                            else: raise Exception(f"Output of {self.module.name} not writeable to output file {self.module.output_file}")
            else:
                self._run_external_command()

            Config.log_success(f"Finished Module: {self.module.name}")                  
            AttackThread.finished_count += 1
            if self.module.analyse_func:
                self._process_analysis()

        except Exception as e:
            Config.log_error(f"Exception in AttackThread ({self.module.name}): \n{traceback.format_exc()}")            
            AttackThread.error_count += 1
        finally:
            AttackThread.running_count -= 1            
            
    def format_switches(self):        
        port_data = Config.target_info.get_port(self.port)
        return [ switch.replace("[protocol]", port_data.protocol if port_data else f"port_{self.port}_no_data")
                .replace("[hostname]", Config.target_info.get_host())
                .replace("[port]", str(self.port))                
                .replace("[outfile]", self.module.output_file)
        for switch in self.module.switches]
        

    def _run_external_command(self):
        """Runs an external command and captures output to a file."""
        try:
            with open(self.module.output_file, "w") as outfile:
                command = [self.module.command] + self.format_switches()
                subprocess.call(" ".join(command),stdout=outfile, stderr=outfile, shell=True)
        except Exception as e:
            Config.log_error(f"Failed to execute external command {self.module.command}: {e}")
            raise

    def _process_analysis(self):
        """Handles analysis of the output after execution."""
        analyse_func = self.return_callable_func(self.module.analyse_func)    
        if analyse_func:
            Config.log_info(f"Running analysis for Module: {self.module.name}")
            if self.output:            
                analyse_func(Config.target_info, self.output)
            elif os.path.exists(self.module.output_file):
                with open(self.module.output_file, 'r') as file:
                    lines = file.readlines()
                    try: # TODO unchecked code
                        loaded_dict = json.loads(str(lines))
                        self.output = loaded_dict
                    except:
                        pass
                    self.output = lines
                    analyse_func(Config.target_info, self.output)
            else: Config.log_warning(f"{self.module.name} did not return usable output for {self.module.analyse_func}")        
