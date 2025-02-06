import curses
import time
import argparse
import signal
import json
from pathlib import Path
from core.config import Config
from core.scan import ScanThread
from core.data_classes import TargetInfo
from ui.commands import send_command
from core.attack_thread import AttackThread
from core.utils import get_hostname_from_url, is_ip_address, get_console_width, truncate_value

def print_info(stdscr, info_list):
    stdscr.addstr("\n\n")
    for data in info_list:
        try:
            stdscr.addstr(f"\n{data}")
        except Exception as e:
            Config.log_error(f"Exception printing info: {e}")


def print_logs(stdscr):
    stdscr.addstr("\n\n" + "\n".join(Config.get_logs()[-15:]))


def exit_handler(sig, frame):
    Config.log_warning("\nCtrl+C detected!")
    Config.target_info.save_to_file()
    exit()

def print_data(data_win):
    data_unordered = Config.target_info.get_ports()
    """Prints formatted data in a window."""
    if not data_unordered:
        data_win.addstr("Waiting for data...\n")
        return

    console_width = get_console_width() - 20
    custom_order = ["protocol", "product", "version", "modules"]
    data = {}

    # Format data based on custom order
    for key, value_dict in data_unordered.items():
        if key == "0": continue
        data[key] = {value_dict_key: value_dict[value_dict_key] for value_dict_key in custom_order}

    headers = ["Ports"] + list(data[next(iter(data))].keys())
    index_width = 5
    column_widths = [index_width] + [max(len(str(header)), max(len(str(row[header])) for row in data.values())) for header in headers[1:]]

    # Dynamically adjust column widths to fit the console window
    while sum(column_widths) > console_width:
        largest_index = column_widths.index(max(column_widths[1:]))
        column_widths[largest_index] -= 1

    # Print headers
    header_line = " | ".join(header.center(width) for header, width in zip(headers, column_widths))
    data_win.addstr(header_line + "\n")
    data_win.addstr("-" * (sum(column_widths) + len(column_widths) * 3 - 1) + "\n")

    # Print data rows
    for key, value in data.items():
        row_line = str(key).ljust(index_width) + " | " + " | ".join(truncate_value(str(value.get(header, '')), width).ljust(width) for header, width in zip(headers[1:], column_widths[1:]))
        data_win.addstr(row_line + "\n")


def main(stdscr):
    curses.noecho()
    curses.cbreak()
    curses.curs_set(1)
    stdscr.nodelay(1)
    stdscr.refresh()

    height, width = stdscr.getmaxyx()
    data_win = curses.newwin(height - 1, width, 0, 0)
    input_win = curses.newwin(1, width, height - 1, 0)
    input_win.nodelay(True)    

    myScan = ScanThread()
    myScan.start()
    
    input_str = ""
    while True:        
        data_win.clear()
        input_win.clear()
        time.sleep(0.01)
        data_win.addstr(f"Modules: Running {AttackThread.running_count}, Finished {AttackThread.finished_count}, Errors {AttackThread.error_count}\n\n")
        print_data(data_win)
        
        if Config.display_data:
            print_info(data_win, Config.display_data)
        else:
            print_logs(data_win)
        
        data_win.refresh()
        
        # Check for user input
        input_win.addstr(f"Enter command: {input_str}")
        ch = input_win.getch()
        if ch == ord('\n'):  # Enter key
            try:
                if input_str == "exit": break
                send_command(input_str)
                input_str = ""
            except ValueError:
                input_str = ""
        elif ch == ord('\b') or ch == 127:  # Backspace
            input_str = input_str[:-1]
        elif ch != -1:
            input_str += chr(ch)
        input_win.refresh()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', help='Path to store output files', required=False)
    parser.add_argument('-t', "--target", help='Target IP or hostname', required=True)
    parser.add_argument("--banner", help='Show welcome banner', action='store_true')
    parser.add_argument('-n', "--newsession", action='store_true', help='New session, do not use saved session data')
    args = parser.parse_args()

    Config.path = Path(args.path) if args.path else Path(args.target)
    Config.path = Config.path.resolve()
    Config.path.mkdir(parents=True, exist_ok=True)
    Config.load_modules("modules.yml")

    target_info = None
    saved_file = Config.path / "pyae_save.json"
    if not args.newsession and saved_file.exists():
        try:
            with open(saved_file) as file:
                Config.target_info = TargetInfo.from_dict(json.load(file))
                Config.log_success(f"[+] Loaded session for {Config.path}")
        except Exception as e:
            Config.log_error(f"Exception loading session: {e}")

    if Config.target_info is None:
        target = args.target
        ip = target if is_ip_address(target) else ""
        hostname_from_url = get_hostname_from_url(target)
        if hostname_from_url and get_hostname_from_url != ip:
            hostname = hostname_from_url
        else: hostname=""
        # Erzeuge eine neue TargetInfo-Instanz, wenn keine Session vorhanden ist
        Config.target_info = TargetInfo(config=Config, ip=ip, hostname=hostname)
        

    if args.banner:
        from ui.banner import animation_loop
        curses.wrapper(animation_loop)
    
    signal.signal(signal.SIGINT, exit_handler)
    curses.wrapper(main)