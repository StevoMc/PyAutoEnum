import threading
import subprocess

class AttackThread (threading.Thread):
    path = ""
    def __init__(self, name, port, command):
        threading.Thread.__init__(self)
        self.name = name
        self.command = command
        self.filename = AttackThread.path + self.name+".txt"
        self.finished = False
        self.got_output = False

    def run(self):
        with open(self.filename, "w") as outfile:
            print(self.command)

            try:
                subprocess.call(self.command, stdout=outfile, stderr=outfile)
                self.finished=True
            except subprocess.CalledProcessError as e:
                print("Error:", e)

    def get_output(self):
        if self.finished == False:
            return None

        with open(self.filename, 'r') as file:
            return file.read()

