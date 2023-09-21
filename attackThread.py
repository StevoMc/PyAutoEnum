import threading
import subprocess
import os
import time
import signal
from utils import log_info,log_error
import traceback
from datacontainer import *

class AttackThread(threading.Thread):
    running_count = 0
    finished_count = 0
    error_count = 0

    def __init__(self, name, port, command, command_args=[], command_kwargs={}, analyse=None):
        """Initialisiert den Thread mit den gegebenen Parametern."""
        super().__init__()
        self.name = name
        self.port = port
        if isinstance(command,list):
            command = " ".join(command)
        self.command = command
        self.command_args = command_args
        self.command_kwargs = command_kwargs
        self.filename = os.path.join(get_working_dir(), f"{self.name}.txt")
        self.daemon = True
        self.output = None
        self.analyse = analyse

    def run(self):
        from scan import check_module_finished
        if check_module_finished(self.name, self.port):
            AttackThread.finished_count+=1
            return

        log_info(f"Started Module: {self.name}")
        AttackThread.running_count += 1
        try:
            # Starter for functions
            if callable(self.command):
                self.output = self.command(*self.command_args, **self.command_kwargs)
            else: # Starter for external programs
                with open(self.filename, "w") as outfile:
                    self.process = subprocess.call(self.command, stdout=outfile, stderr=outfile, shell=True)
            log_info(f"Finished {self.name}")
            from scan import complete_module
            complete_module(self.name, self.port)
            AttackThread.finished_count += 1
        except:
            e = traceback.format_exc()
            log_error(f"Exception in attackThread.py: {e}")
            AttackThread.errors_count += 1
        finally:
            AttackThread.running_count -= 1
            if callable(self.analyse):
                if not self.output:
                    if os.path.exists(self.filename):
                        with open(self.filename, 'r') as file:
                            self.output = file.readlines()
                self.analyse(self.output)
