import threading

class ScanThread (threading.Thread):
    def __init__(self, target):
        threading.Thread.__init__(self)
        self.target= target
        self.finished = False

    def run(self):
        start_scan(self.target)
        self.finished = True
