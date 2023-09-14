import threading
import time
from scan import start_scan
from utils import log_error
import traceback

class ScanThread (threading.Thread):
    def __init__(self, target, open_ports_save):
        threading.Thread.__init__(self)
        self.target= target
        self.open_ports_save = open_ports_save
        self.finished = False
        self.daemon = True

    def run(self):
        try:
            start_scan(self.target, self.open_ports_save)
            self.finished = True
        except: 
            stack_trace_str = traceback.format_exc()
            log_error(f"Exception in scanThread: {stack_trace_str}")

