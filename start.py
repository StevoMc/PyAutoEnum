import curses
import time
import argparse
from scan import *

REFRESH_PER_MINUTE = 60
stdscr = None

scans= []

def print_logs(stdscr, logs):
    for line in logs:
        stdscr.addstr(line+"\n")


def print_data(stdscr,data):
    if not data:
        return

    # Calculate column widths based on headers and data
    headers = list(data[next(iter(data))].keys())
    column_widths = [max(len(str(header)), max(len(str(row[header])) for row in data.values())) for header in headers]

    stdscr.clear()
    stdscr.move(0, 0)
    # Print headers
    header_line = " | ".join(header.center(width) for header, width in zip(headers, column_widths))
    stdscr.addstr(header_line + "\n")
    stdscr.addstr("-" * (sum(column_widths) + len(column_widths) * 3 - 1) + "\n")

    # Print data rows
    for value in data.values():
        row_line = " | ".join(str(value.get(header, '')).ljust(width) for header, width in zip(headers, column_widths))
        stdscr.addstr(row_line + "\n")

    stdscr.refresh()

def input_bar(stdscr):
    input_row = curses.LINES - 1
    stdscr.move(input_row, 0)
    stdscr.addstr(input_row, 0, "Enter command: ")
    stdscr.refresh()

    curses.curs_set(1)  # Show the cursor
    stdscr.nodelay(1)   # Enable non-blocking input
    user_input = ""

    while True:
        try:
            char = stdscr.getch()

            if char == -1:  # No input
                continue
            elif char == 10:  # Enter key
                break
            elif char == 27:  # Escape key
                user_input = "exit"
                break
            else:
                user_input += chr(char)
                stdscr.addch(char)

            stdscr.refresh()
        except curses.error:
            pass

    curses.curs_set(0)  # Hide the cursor
    stdscr.nodelay(0)   # Disable non-blocking input
    stdscr.clrtoeol()   # Clear the input line
    stdscr.refresh()

    return user_input.lower()

def main():
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

    #Start Scan
    myScan = ScanThread(args.t)
    myScan.start()
    scans.append(myScan)

    # Initialise Window
    stdscr = curses.initscr()
    curses.noecho()
    curses.cbreak()
    curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_CYAN, curses.COLOR_BLACK)

    try:
        user_input=""
        while user_input!="exit":
            print_data(stdscr, get_data())
            print_logs(stdscr, get_logs())
            user_input = input_bar(stdscr)
            time.sleep(60 / REFRESH_PER_MINUTE)
    except KeyboardInterrupt:
        pass
    finally:
        curses.echo()
        curses.nocbreak()
        curses.endwin()

if __name__ == "__main__":
    main()
