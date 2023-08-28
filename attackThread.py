import threading
import subprocess
import os
import time
import signal
from utils import write_log

class AttackThread(threading.Thread):
    path = ""

    def __init__(self, name, port, command):
        """Initialisiert den Thread mit den gegebenen Parametern."""
        super().__init__()
        self.name = name
        self.port = port
        if isinstance(command,list):
            command = " ".join(command)
        self.command = command
        self.filename = os.path.join(AttackThread.path, f"{self.name}.txt")
        self.finished = threading.Event()
        self.stop_signal = threading.Event()
        self.process = None
        self.daemon = True

    def run(self):
        try:
            """Führt den angegebenen Befehl aus und speichert die Ausgabe in einer Datei."""
            with open(self.filename, "w") as outfile:
                # Startet den Unterprozess
                self.process = subprocess.call(self.command, stdout=outfile, stderr=outfile, shell=True)
            write_log(f"[+] Finished {self.name}")
            from scan import complete_module
            complete_module(self.name, self.port)
        except:
            e = traceback.format_exc()
            write_log(f"Exception in attackThread.py: {e}")
        finally: self.finished.set()




    def get_output(self):
        """Liest die Ausgabe des Befehls aus der Datei und gibt sie zurück."""
        if not self.finished.is_set():
            return None

        with open(self.filename, 'r') as file:
            return file.read()
