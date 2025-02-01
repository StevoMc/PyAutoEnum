from core.config import Config  # Import here to prevent circular import
import threading
import os

logs = []
logs_lock = threading.Lock()


def log_interaction(text):
    _write_log(f"<{os.getlogin()}> " + str(text))


def log_error(text):
    _write_log("[-] " + str(text))


def log_warning(text):
    _write_log("[!] " + str(text))


def log_info(text):
    _write_log("[*] " + str(text))


def log_success(text):
    _write_log("[+] " + str(text))


def _write_log(text):
    try:      
        # Write the log to the file
        with logs_lock:
            logs.append(str(text))
            with open(Config.path / "logs.txt", "a") as file:
                file.write(str(text) + "\n")

    except Exception as e:
        log_error(f"Error writing log: {str(e)}")


def get_logs():
    return logs
