"""Interface module for the PyAutoEnum application."""

import curses
import threading
import time
from typing import List

from pyautoenum.config.manager import ConfigManager
from pyautoenum.ui.commands import CommandProcessor
from pyautoenum.utils.display import get_console_width, truncate_value


class Interface(threading.Thread):
    """Interactive terminal-based interface for PyAutoEnum."""
    
    def __init__(self):
        """Initialize the interface thread."""
        super().__init__()
        self.daemon = True
        self.stdscr = None
        self.data_win = None
        self.input_win = None
        self.height = 0
        self.width = 0
        self.command_processor = CommandProcessor()
    
    def run(self):
        """Start the interface in a curses wrapper."""
        try:
            curses.wrapper(self._main_loop)
        except Exception as e:
            ConfigManager.log_error(f"Interface error: {str(e)}")
    
    def print_data(self):
        """Print formatted data in the data window."""
        if not self.data_win:
            return
        
        if not ConfigManager.target_info:
            self.data_win.clear()
            self.data_win.addstr("No target information available.")
            self.data_win.refresh()
            return
            
        data_unordered = ConfigManager.target_info.get_ports_dict_data()
        if not data_unordered:
            self.data_win.clear()
            self.data_win.addstr("No port data available yet.")
            self.data_win.refresh()
            return

        console_width = get_console_width() - 20
        custom_order = ["protocol", "product", "version", "modules"]
        data = {}

        # Format data based on custom order
        for key, value_dict in data_unordered.items():
            data[key] = {header: value_dict.get(header, "") for header in custom_order}

        headers = ["Ports"] + list(data[next(iter(data))].keys())
        index_width = 5
        column_widths = [index_width] + [
            max(len(str(header)), max(len(str(row.get(header, ""))) for row in data.values()))
            for header in headers[1:]
        ]

        # Dynamically adjust column widths to fit the console width
        while sum(column_widths) > console_width and min(column_widths) > 10:
            # Find the widest column and reduce its width
            max_width_index = column_widths.index(max(column_widths))
            column_widths[max_width_index] -= 1

        self.data_win.clear()
        
        # Print headers
        header_line = " | ".join(
            header.center(width) for header, width in zip(headers, column_widths)
        )
        self.data_win.addstr(header_line + "\n")
        self.data_win.addstr("-" * (sum(column_widths) + len(column_widths) * 3 - 1) + "\n")

        # Print data rows
        for key, value in data.items():
            row = [str(key).ljust(index_width)]
            for header, width in zip(headers[1:], column_widths[1:]):
                val = value.get(header, "")
                row.append(truncate_value(str(val), width).ljust(width))
            self.data_win.addstr(" | ".join(row) + "\n")
            
        self.data_win.refresh()
    
    def print_logs(self):
        """Print recent logs in the data window."""
        if not self.data_win:
            return
            
        self.data_win.clear()
        self.data_win.addstr("\n\n" + "\n".join(ConfigManager.get_logs()[-15:]))
        self.data_win.refresh()
    
    def print_info(self, info_list: List[str]):
        """Print information in the data window."""
        if not self.data_win:
            return
            
        self.data_win.clear()
        self.data_win.addstr("\n\n")
        for data in info_list:
            self.data_win.addstr(f"{data}\n")
        self.data_win.refresh()
    
    def _main_loop(self, stdscr):
        """Main interface loop handling user input and display."""
        self.stdscr = stdscr
        
        curses.noecho()
        curses.cbreak()
        curses.curs_set(1)
        self.stdscr.nodelay(1)
        self.stdscr.refresh()

        self.height, self.width = self.stdscr.getmaxyx()
        self.data_win = curses.newwin(self.height - 1, self.width, 0, 0)
        self.input_win = curses.newwin(1, self.width, self.height - 1, 0)
        self.input_win.nodelay(True)

        input_str = ""
        
        while True:
            # Handle window resize
            try:
                new_height, new_width = self.stdscr.getmaxyx()
                if new_height != self.height or new_width != self.width:
                    self.height, self.width = new_height, new_width
                    self.stdscr.clear()
                    self.data_win = curses.newwin(self.height - 1, self.width, 0, 0)
                    self.input_win = curses.newwin(1, self.width, self.height - 1, 0)
                    self.input_win.nodelay(True)
                    self.stdscr.refresh()
            except curses.error:
                pass
                
            # Update display
            if ConfigManager.display_data:
                self.print_info(ConfigManager.display_data)
            else:
                self.print_data()
                
            # Process user input
            self.input_win.clear()
            self.input_win.addstr(f"> {input_str}")
            self.input_win.refresh()
            
            try:
                key = self.input_win.getch()
                if key != -1:  # If a key was pressed
                    if key == curses.KEY_ENTER or key == 10 or key == 13:  # Enter key
                        if input_str:
                            self.command_processor.execute_command(input_str)
                        input_str = ""
                    elif key == curses.KEY_BACKSPACE or key == 127:  # Backspace
                        input_str = input_str[:-1]
                    elif key == curses.KEY_RESIZE:
                        pass  # Handle resize separately
                    elif 32 <= key <= 126:  # Printable ASCII
                        input_str += chr(key)
            except curses.error:
                pass
                
            time.sleep(0.02)  # Small delay to prevent CPU hogging
