"""Simplified interface for PyAutoEnum that uses curses in a more basic way."""

import curses
import sys
import threading
import time
from datetime import datetime, timedelta
from typing import List

from pyautoenum.config.manager import ConfigManager
from pyautoenum.ui.commands import CommandProcessor


class SimpleInterface(threading.Thread):
    """A simplified curses-based interface for PyAutoEnum."""
    
    def __init__(self):
        """Initialize the interface thread."""
        super().__init__()
        self.daemon = True
        self.stdscr = None
        self.running = True
        self.command_processor = CommandProcessor()
        self._commands_history = []
        self._current_command = ""
        
    def run(self):
        """Start the interface and initialize curses."""
        try:
            # Basic terminal check
            import os
            if not os.isatty(sys.stdout.fileno()):
                ConfigManager.log_error("Not running in a terminal, cannot start UI.")
                return
                
            # Initialize curses with wrapper for safe cleanup
            curses.wrapper(self._main)
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            ConfigManager.log_error(f"Interface error: {str(e)}\n{error_trace}")
            
    def switch_mode(self, mode: str):
        """Compatibility method for the standard interface."""
        pass
        
    def set_info_data(self, data: List[str]):
        """Compatibility method for the standard interface."""
        pass
        
    def show_help(self):
        """Show help information."""
        help_commands = [
            "help              - Show this help",
            "scan              - Show current scan progress",
            "ports             - Show discovered ports and services",
            "logs              - Show recent log messages",
            "quit, exit        - Exit the application",
            "clear             - Clear the screen",
        ]
        self._draw_info("PyAutoEnum Help", help_commands)
        
    def set_status(self, message: str):
        """Set status message (compatibility method)."""
        pass
        
    def _main(self, stdscr):
        """Main interface loop."""
        self.stdscr = stdscr
        self.height, self.width = stdscr.getmaxyx()
        
        # Configure terminal
        curses.curs_set(1)  # Show cursor
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_GREEN, -1)  # Success
        curses.init_pair(2, curses.COLOR_RED, -1)    # Error
        curses.init_pair(3, curses.COLOR_YELLOW, -1) # Warning
        curses.init_pair(4, curses.COLOR_BLUE, -1)   # Info
        
        # Draw initial screen
        self._draw_welcome()
        
        # Main loop
        input_line = ""
        cursor_pos = 0
        
        while self.running:
            # Update the screen
            self.stdscr.clear()
            
            # Draw a very simple header
            header = "=== PyAutoEnum ==="
            self.stdscr.addstr(0, (self.width - len(header)) // 2, header, curses.A_BOLD)
            
            # Draw status info
            status_line = f"Target: {ConfigManager.target_info.get_host() if ConfigManager.target_info else 'None'}"
            self.stdscr.addstr(1, 0, status_line)
            
            # Show recent logs
            if ConfigManager.get_logs():
                max_logs = min(10, len(ConfigManager.get_logs()))
                recent_logs = ConfigManager.get_logs()[-max_logs:]
                for i, log in enumerate(recent_logs):
                    color = curses.A_NORMAL
                    if log.startswith("[+]"):
                        color = curses.color_pair(1)
                    elif log.startswith("[-]"):
                        color = curses.color_pair(2)
                    elif log.startswith("[!]"):
                        color = curses.color_pair(3)
                    elif log.startswith("[*]"):
                        color = curses.color_pair(4)
                    self.stdscr.addstr(3 + i, 2, log[:self.width-4], color)
                
            # Draw ports data if available
            if ConfigManager.target_info and ConfigManager.target_info.ports:
                ports_count = len(ConfigManager.target_info.ports)
                self.stdscr.addstr(self.height - 5, 0, f"Discovered Ports: {ports_count}")
                
            # Draw command prompt
            prompt = "> "
            self.stdscr.addstr(self.height - 2, 0, prompt)
            self.stdscr.addstr(self.height - 2, len(prompt), input_line)
            
            # Position cursor
            self.stdscr.move(self.height - 2, len(prompt) + cursor_pos)
            
            # Refresh the screen
            self.stdscr.refresh()
            
            # Get user input
            try:
                key = self.stdscr.getch()
                
                if key == curses.KEY_ENTER or key == 10 or key == 13:  # Enter key
                    if input_line.strip():
                        # Execute the command
                        self.command_processor.execute_command(input_line.strip())
                        self._commands_history.append(input_line.strip())
                        input_line = ""
                        cursor_pos = 0
                elif key == curses.KEY_BACKSPACE or key == 127:  # Backspace
                    if cursor_pos > 0:
                        input_line = input_line[:cursor_pos-1] + input_line[cursor_pos:]
                        cursor_pos -= 1
                elif key == curses.KEY_LEFT:  # Left arrow
                    cursor_pos = max(0, cursor_pos - 1)
                elif key == curses.KEY_RIGHT:  # Right arrow
                    cursor_pos = min(len(input_line), cursor_pos + 1)
                elif key == curses.KEY_UP:  # Up arrow - command history
                    if self._commands_history:
                        input_line = self._commands_history[-1]
                        cursor_pos = len(input_line)
                elif 32 <= key <= 126:  # Printable ASCII
                    input_line = input_line[:cursor_pos] + chr(key) + input_line[cursor_pos:]
                    cursor_pos += 1
            except Exception as e:
                ConfigManager.log_error(f"Input error: {str(e)}")
                
            time.sleep(0.05)  # Small delay
            
    def _draw_welcome(self):
        """Draw a welcome screen."""
        welcome_text = [
            "",
            "PyAutoEnum - Automated Enumeration Tool",
            "====================================",
            "",
            "Type 'help' for available commands.",
            "Press Ctrl+C to exit."
        ]
        
        self._draw_info("Welcome", welcome_text)
        
    def _draw_info(self, title: str, text_lines: List[str]):
        """Draw information on the screen."""
        if not self.stdscr:
            return
            
        self.stdscr.clear()
        
        # Draw title
        self.stdscr.addstr(1, 2, title, curses.A_BOLD)
        
        # Draw text lines
        for i, line in enumerate(text_lines):
            self.stdscr.addstr(3 + i, 2, line)
            
        self.stdscr.refresh()
