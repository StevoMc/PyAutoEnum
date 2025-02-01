import threading
import subprocess
from core.utils import log_info, log_error
from core.config import Config
from typing import Callable, List, Optional


class AttackThread(threading.Thread):
    running_count = 0
    finished_count = 0
    error_count = 0

    def __init__(self, name, port, command, command_args=[], command_kwargs={}, analyse=None):
        if command_args is None:
            command_args = []
        if command_kwargs is None:
            command_kwargs = {}

        super().__init__()
        self.name = name.replace(" ","_")
        self.filename = Config.path / f"{self.name}.txt"
        self.port = port        
        self.command = command
        self.command_args = [arg.replace("[path]", str(self.filename)) for arg in command_args]
        self.command_kwargs = command_kwargs        
        self.daemon = True
        self.output = None
        self.analyse = analyse

    def run(self):
        """Runs the attack process in the thread."""
        from core.scan_manager import complete_module
        try:
            log_info(f"Started Module: {self.name}")
            AttackThread.running_count += 1

            # Run command (either callable or external process)
            if callable(self.command):

                self.output = self.command(*self.command_args, **self.command_kwargs)
            else:
                self._run_external_command()

            log_info(f"Finished {self.name}")
            complete_module(self.name, self.port)
            AttackThread.finished_count += 1

        except Exception as e:
            log_error(f"Exception in attackThread.py: {e}")
            AttackThread.error_count += 1
        finally:
            AttackThread.running_count -= 1
            self._process_analysis()

    def _run_external_command(self):
        """Runs the external command and captures output to a file."""
        try:
            with open(self.filename, "w") as outfile:
                self.process = subprocess.call(self.command, stdout=outfile, stderr=outfile, shell=True)
        except Exception as e:
            log_error(f"Failed to execute external command {self.command}: {e}")
            raise

    def _process_analysis(self):
        """Handles analysis of the output after execution."""
        if callable(self.analyse):
            if not self.output and self.filename.exists():
                with open(self.filename, 'r') as file:
                    self.output = file.readlines()
            self.analyse(self.output)
