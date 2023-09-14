import curses
import time
import argparse
import threading
from scan import *
from scanThread import ScanThread
import traceback
import signal
import sys
import json


def print_info(stdscr, info_list):
    stdscr.addstr(f"\n\n")
    try:
        for data in info_list[offset:]:
            stdscr.addstr(f"\n{data}")
    except: pass


def print_logs(stdscr, logs):
    stdscr.addstr("\n\n"+"\n".join(logs[-15:]))


def print_data(data_win,data_unordered):

    if not data_unordered:
        data_win.addstr("Waiting for data...\n")
        return

    console_width = get_console_width() - 20
    custom_order = ["service", "product", "version", "modules"]
    data = {}
    for key,value_dict in data_unordered.items():
        if key == "0": continue
        data[key] = {value_dict_key:value_dict[value_dict_key] for value_dict_key in custom_order}

    # Calculate column widths based on headers and data
    headers = ["Ports"]+list(data[next(iter(data))].keys())
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
        row_line = str(key).ljust(index_width) + " | " + " | ".join(truncate_value(str(value.get(header, '')),width).ljust(width) for header, width in zip(headers[1:], column_widths[1:]))
        data_win.addstr(row_line + "\n")

def save_data():
    try:
        #Save Progress
        with open_ports_lock:
            with open(get_working_dir()+"pyae_save.json","w") as file:
                json.dump(get_data(),file)
    except:
        e = traceback.format_exc()
        log_error(f"Exception in save_data: {e}")



def exit_handler(sig, frame):
    log_warning("\nCtrl+C detected!")
    save_data()
    exit()


def main(stdscr,target):
    # Initialise Window
    stdscr = curses.initscr()
    stdscr.nodelay(1)
    stdscr.refresh()
    curses.noecho()
    curses.cbreak()
    stdscr.move(0,0)
    height, width = stdscr.getmaxyx()
    data_win_height = height - 1
    data_win = curses.newwin(data_win_height, width, 0, 0)
    input_win = curses.newwin(1, width, data_win_height, 0)
    input_win.nodelay(True)
    data_win.clear()
    input_win.clear()

    #Start Scan
    myScan = ScanThread(target,open_ports_save)
    myScan.start()

    counter=0
    global offset
    try:
        input_str = ""
        while True:
            input_win.clear()
            data_win.clear()
            time.sleep(0.01)
            data_win.addstr(f"Modules: {AttackThread.running_count} running, {AttackThread.finished_count} finished, {AttackThread.error_count} errors\n\n")
            print_data(data_win, get_data())
            display_data = get_display_data()
            if display_data: print_info(data_win, display_data)
            else: print_logs(data_win, get_logs())
            data_win.refresh()

            #Check for user input
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

    except:
        e = traceback.format_exc()
        log_error(f"Exception in start.py: {e}")
    finally: save_data()

if __name__ == "__main__":
    #Parse Arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--path', help='Path to store the output files', required=False)
    parser.add_argument('-t',"--target", help='Target ip or hostname', required=True)
    parser.add_argument('-n',"--newsession",  action='store_true', help='New Session, do not use saved session data', required=False)
    args = parser.parse_args()

    if args.path != None:
        if not args.path.endswith('/'):
            path = args.path + '/'
        else:
            path = args.path
    else:
        path = f"{args.target}/"

    if os.path.isdir(path) == False:
        os.makedirs(path)

    open_ports_save = {}
    if not args.newsession:
        if os.path.exists(path+"pyae_save.json"):
            try:
                with open(path+"pyae_save.json") as file:
                    open_ports_save = json.load(file)
                    if open_ports_save:
                        log_success(f"[+] Loaded session for {path}")
            except:
                e = traceback.format_exc()
                log_error(f"Exception in load session: {e}")
    else:
        # Display Banner
        from banner import animation_loop
        curses.wrapper(animation_loop)

    set_working_dir(path)
    signal.signal(signal.SIGINT, exit_handler)

    curses.wrapper(main,args.target)
