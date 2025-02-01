import curses
import time
import argparse
import signal
import json
from pathlib import Path
from core.config import *
from core.logging_utils import get_logs
from core.scan_manager import *


def print_info(stdscr, info_list):
    """Prints the given info list to the stdscr window."""
    stdscr.addstr("\n\n")
    for data in info_list:
        try:
            stdscr.addstr(f"\n{data}")
        except Exception as e:
            log_error(f"Exception printing info: {e}")


def print_logs(stdscr, logs):
    """Prints the last 15 logs to the stdscr window."""
    stdscr.addstr("\n\n" + "\n".join(logs[-15:]))


def print_data(data_win, data_unordered):
    """Prints formatted data in a window."""
    if not data_unordered:
        data_win.addstr("Waiting for data...\n")
        return

    console_width = get_console_width() - 20
    custom_order = ["service", "product", "version", "modules"]
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


def save_data():
    """Saves the session data to a file."""
    try:
        with open_ports_lock:
            save_path = Config.path / "pyae_save.json"
            with open(save_path, "w") as file:
                json.dump(get_data(), file)
    except Exception as e:
        log_error(f"Exception in save_data: {e}")


def exit_handler(sig, frame):
    """Handles exit signals."""
    log_warning("\nCtrl+C detected!")
    save_data()
    exit()


def main(stdscr, target, ports):
    """Main function that runs the curses UI and manages the scanning process."""
    # Initialise Window
    stdscr = curses.initscr()
    stdscr.nodelay(1)
    stdscr.refresh()
    curses.noecho()
    curses.cbreak()
    stdscr.move(0, 0)
    height, width = stdscr.getmaxyx()
    data_win_height = height - 1
    data_win = curses.newwin(data_win_height, width, 0, 0)
    input_win = curses.newwin(1, width, data_win_height, 0)
    input_win.nodelay(True)
    data_win.clear()
    input_win.clear()

    # Start Scan
    myScan = ScanThread(target, ports, open_ports_save)
    myScan.start()

    counter = 0
    global offset
    try:
        input_str = ""
        while True:
            input_win.clear()
            data_win.clear()
            time.sleep(0.01)
            data_win.addstr(f"Modules: {AttackThread.running_count} running, {AttackThread.finished_count} finished, {AttackThread.error_count} errors\n\n")
            print_data(data_win, get_data())
            display_data = Config.display_data
            if display_data:
                print_info(data_win, display_data)
            else:
                print_logs(data_win, get_logs())
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

    except Exception as e:
        log_error(f"Exception in pyautoenum.py: {e}")
    finally:
        save_data()


if __name__ == "__main__":
    """Main entry point for the program."""
    # Parse Arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', help='Path to store the output files', required=False)
    parser.add_argument('-t', "--target", help='Target ip or hostname', required=True)
    parser.add_argument("--banner", help='Show welcome banner')
    parser.add_argument('-n', "--newsession", action='store_true', help='New Session, do not use saved session data', required=False)
    parser.add_argument('-p', "--ports", help='Target ports', required=False)

    args = parser.parse_args()

    # Init Config
    Config.path = Path(args.path) if args.path else Path(args.target)
    Config.path = Config.path.resolve()

    # Ensure the directory exists
    if not Config.path.exists():
        Config.path.mkdir(parents=True)

    Config.modules = load_modules("modules.yml")
    
    
    open_ports_save = {}
    if not args.newsession:
        saved_file = Config.path / "pyae_save.json"
        if saved_file.exists():
            try:
                with open(saved_file) as file:
                    open_ports_save = json.load(file)
                    if open_ports_save:
                        log_success(f"[+] Loaded session for {Config.path}")
            except Exception as e:
                log_error(f"Exception in load session: {e}")
    elif args.banner:
        # Display Banner
        from ui.banner import animation_loop
        curses.wrapper(animation_loop)

    signal.signal(signal.SIGINT, exit_handler)
    curses.wrapper(main, args.target, args.ports)
