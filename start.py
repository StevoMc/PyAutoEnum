import curses
import time
import argparse
import threading
from scan import *
from scanThread import ScanThread

def print_logs(stdscr, logs):
    stdscr.addstr("\n\n"+"\n".join(logs[-15:]))


def print_data(data_win,data):

    if not data:
        data_win.addstr("No data")
        return

    # Calculate column widths based on headers and data
    headers = ["Ports"]+list(data[next(iter(data))].keys())
    index_width = 5
    column_widths = [index_width] + [max(len(str(header)), max(len(str(row[header])) for row in data.values())) for header in headers[1:]]

    # Print headers
    header_line = " | ".join(header.center(width) for header, width in zip(headers, column_widths))
    data_win.addstr(header_line + "\n")
    data_win.addstr("-" * (sum(column_widths) + len(column_widths) * 3 - 1) + "\n")

    # Print data rows
    for key, value in data.items():
        row_line = str(key).ljust(index_width) + " | " + " | ".join(str(value.get(header, '')).ljust(width) for header, width in zip(headers[1:], column_widths[1:]))
        data_win.addstr(row_line + "\n")


def main(stdscr):
    global tasks
    #Parse Arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--path', help='Path to store the output files', required=False)
    parser.add_argument('-t', help='Target ip or hostname', required=True)
    args = parser.parse_args()

    if args.path != None:
        if not args.path.endswith('/'):
            at.path = args.path + '/'
        else:
            at.path = args.path
    else:
        at.path = f"{args.t}/"

    if os.path.isdir(at.path) == False:
        os.makedirs(at.path)

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
    myScan = ScanThread(args.t)
    myScan.start()

    counter=0
    try:
        user_input = ""
        input_str = ""
        while user_input != "exit":
            input_win.clear()
            data_win.clear()
            time.sleep(0.1)
            print_data(data_win, get_data())
            print_logs(data_win, get_logs())
#            write_log(str(counter))
#            counter+=1
            data_win.refresh()

            #Check for user input
            input_win.addstr(f"Enter command: {input_str}")
            ch = input_win.getch()
            if ch == ord('\n'):  # Enter key
                try:
                    user_input = input_str
                    input_str = ""
                except ValueError:
                    input_str = ""
            elif ch == ord('\b') or ch == 127:  # Backspace
                input_str = input_str[:-1]
            elif ch != -1:
                input_str += chr(ch)
            input_win.refresh()

    except Exception as e:
        write_log(e)

if __name__ == "__main__":
    curses.wrapper(main)
