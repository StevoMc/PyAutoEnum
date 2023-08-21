import threading
import subprocess
import os
import time
import signal

class AttackThread(threading.Thread):
    path = ""

    def __init__(self, name, port, command):
        """Initialisiert den Thread mit den gegebenen Parametern."""
        super().__init__()
        self.name = name
        self.command = command
        self.filename = os.path.join(AttackThread.path, f"{self.name}.txt")
        self.finished = threading.Event()
        self.stop_signal = threading.Event()
        self.process = None
        self.daemon = True

    def run(self):
        """Führt den angegebenen Befehl aus und speichert die Ausgabe in einer Datei."""
        with open(self.filename, "w") as outfile:

                # Startet den Unterprozess
                self.process = subprocess.Popen(self.command, stdout=outfile, stderr=outfile, shell=True, preexec_fn=os.setsid)

                # Wartet, bis der Prozess beendet ist oder ein Stopp-Signal empfangen wird
                while self.process.poll() is None:
                    time.sleep(0.1)

                    # Wenn ein Stopp-Signal empfangen wird und der Prozess noch läuft, wird der Prozess beendet
                    if self.stop_signal.is_set():
                        try:
                            os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                            self.process.wait()
                        except ProcessLookupError:
                            pass
                self.finished.set()

    def stop(self):
        """Sendet ein Signal an den Thread, um den Prozess zu stoppen."""
        self.stop_signal.set()
        if self.process:
            os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            self.process.wait()

    def get_output(self):
        """Liest die Ausgabe des Befehls aus der Datei und gibt sie zurück."""
        if not self.finished.is_set():
            return None

        with open(self.filename, 'r') as file:
            return file.read()
