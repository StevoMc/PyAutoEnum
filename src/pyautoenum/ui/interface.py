"""Interface module for the PyAutoEnum application."""

import curses
import sys
import threading
import time
from datetime import timedelta
from typing import Any, Dict, List, Optional, Tuple

from pyautoenum.config.manager import ConfigManager
from pyautoenum.core.attack_thread import attack_thread_pool
from pyautoenum.ui.commands import CommandProcessor
from pyautoenum.utils.display import get_console_width, truncate_value


class UIMode:
    """Enum-like class for different UI modes."""
    PORT_DATA = "port_data"
    LOGS = "logs"
    INFO = "info"
    SCAN_PROGRESS = "scan_progress"
    HELP = "help"


class Interface(threading.Thread):
    """Interactive terminal-based interface for PyAutoEnum."""
    
    def __init__(self):
        """Initialize the interface thread."""
        super().__init__()
        self.daemon = True
        self.stdscr = None
        self.data_win = None
        self.status_win = None
        self.input_win = None
        self.height = 0
        self.width = 0
        self.command_processor = CommandProcessor()
        self._ui_mode = UIMode.PORT_DATA
        self._display_data = []
        self._status_message = ""
        self._last_update = 0
        self._update_interval = 0.5  # seconds
        self._colors_initialized = False
    
    def run(self):
        """Start the interface in a curses wrapper."""
        try:
            # Check if terminal supports curses
            import os
            term = os.environ.get("TERM")
            if not term:
                ConfigManager.log_error("No TERM environment variable set. Curses requires a valid terminal type.")
                return
                
            # Check if we're running in a proper terminal
            if not os.isatty(sys.stdout.fileno()):
                ConfigManager.log_error("Not running in an interactive terminal. UI cannot be displayed.")
                return
                
            ConfigManager.log_info(f"Initializing UI with terminal type: {term}")
            
            # Debug info about the environment
            ConfigManager.log_info(f"Python version: {sys.version}")
            ConfigManager.log_info(f"Curses version: {curses.version if hasattr(curses, 'version') else 'unknown'}")
            
            # Use curses wrapper for proper terminal cleanup
            curses.wrapper(self._main_loop)
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            ConfigManager.log_error(f"Interface initialization error: {str(e)}\n{error_trace}")
            error_trace = traceback.format_exc()
            ConfigManager.log_error(f"Interface initialization error: {str(e)}\n{error_trace}")
    
    def switch_mode(self, mode: str):
        """Switch the UI display mode."""
        self._ui_mode = mode
        self._last_update = 0  # Force immediate update
    
    def set_info_data(self, data: List[str]):
        """Set data to display in info mode."""
        self._display_data = data
        if data:
            self.switch_mode(UIMode.INFO)
    
    def show_help(self):
        """Show help information."""
        help_text = [
            "PyAutoEnum - Help",
            "===============================",
            "Available commands:",
            "  help              - Show this help",
            "  scan              - Show current scan progress",
            "  ports             - Show discovered ports and services",
            "  logs              - Show recent log messages",
            "  quit, exit        - Exit the application",
            "  clear             - Clear the screen",
            "",
            "Use <TAB> to cycle through view modes",
            "Press <Ctrl+C> to exit"
        ]
        self.set_info_data(help_text)
        self.switch_mode(UIMode.HELP)
    
    def set_status(self, message: str):
        """Set the status message."""
        self._status_message = message
        
    def _setup_colors(self):
        """Initialize color pairs for the UI."""
        if not self._colors_initialized:
            try:
                if curses.has_colors():
                    curses.start_color()
                    curses.use_default_colors()
                    
                    # Define color pairs
                    # 1: Status bar
                    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)
                    # 2: Headers
                    curses.init_pair(2, curses.COLOR_CYAN, -1)
                    # 3: Success/positive
                    curses.init_pair(3, curses.COLOR_GREEN, -1)
                    # 4: Warning
                    curses.init_pair(4, curses.COLOR_YELLOW, -1)
                    # 5: Error/danger
                    curses.init_pair(5, curses.COLOR_RED, -1)
                    # 6: Info
                    curses.init_pair(6, curses.COLOR_BLUE, -1)
                    # 7: Highlight
                    curses.init_pair(7, curses.COLOR_BLACK, curses.COLOR_WHITE)
                    
                    self._colors_initialized = True
                    ConfigManager.log_info("Color support initialized")
                else:
                    ConfigManager.log_warning("Terminal doesn't support colors")
            except Exception as e:
                ConfigManager.log_error(f"Failed to initialize colors: {str(e)}")
                # Continue without colors
    
    def _draw_status_bar(self):
        """Draw the status bar."""
        if not self.status_win:
            return
            
        self.status_win.clear()
        
        # Create status bar content
        mode_text = f"Mode: {self._ui_mode.replace('_', ' ').title()}"
        status_text = self._status_message or "Ready"
        help_text = "TAB: Switch View | F1: Help | Ctrl+C: Quit"
        
        # Calculate spacing
        available_width = self.width - len(mode_text) - len(help_text) - 2
        status = truncate_value(status_text, available_width).ljust(available_width)
        status_line = f"{mode_text} {status} {help_text}"
        
        # Draw status bar with color
        self.status_win.bkgd(' ', curses.color_pair(1))
        self.status_win.addstr(0, 0, status_line)
        self.status_win.refresh()
    
    def _draw_progress_bar(self, win, y: int, x: int, width: int, 
                          progress: float, color_pair: int = 3) -> None:
        """Draw a progress bar in the window."""
        try:
            # Draw the progress bar frame
            win.addch(y, x, '[')
            win.addch(y, x + width - 1, ']')
            
            # Calculate filled portion
            filled_width = int((width - 2) * (progress / 100))
            
            # Draw filled portion
            win.attron(curses.color_pair(color_pair))
            for i in range(filled_width):
                win.addch(y, x + 1 + i, ' ', curses.A_REVERSE)
            win.attroff(curses.color_pair(color_pair))
        except Exception:
            # Silently fail if drawing fails
            pass
    
    def _format_time(self, seconds: float) -> str:
        """Format time in seconds to a readable string."""
        td = timedelta(seconds=int(seconds))
        hours, remainder = divmod(td.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    
    def _safe_addstr(self, win, y, x, text, attr=0):
        """Safely add a string to a window, handling exceptions."""
        if not win:
            return False
        try:
            # Make sure text is a string
            str_text = str(text)
            # Make sure we're not writing outside the window
            h, w = win.getmaxyx()
            if y >= h or x >= w:
                return False
                
            # Truncate the text if it would go past the window edge
            max_len = w - x - 1
            if len(str_text) > max_len:
                str_text = str_text[:max_len]
                
            # Write the string
            win.addstr(y, x, str_text, attr)
            return True
        except Exception:
            return False

    def _update_display(self):
        """Update the display based on current mode."""
        if not self.data_win:
            return
            
        try:
            # Skip updates if it's too soon since the last update
            current_time = time.time()
            if current_time - self._last_update < self._update_interval and self._last_update > 0:
                return
            self._last_update = current_time
            
            # Clear the display window
            self.data_win.clear()
            
            # Handle different modes
            if self._ui_mode == UIMode.PORT_DATA:
                self.print_data()
            elif self._ui_mode == UIMode.LOGS:
                self.print_logs()
            elif self._ui_mode == UIMode.INFO:
                self.print_info(self._display_data)
            elif self._ui_mode == UIMode.SCAN_PROGRESS:
                self.print_scan_progress()
            elif self._ui_mode == UIMode.HELP:
                self.print_info(self._display_data)
            
            self.data_win.refresh()
        except Exception as e:
            # Don't crash on display errors
            try:
                self.data_win.clear()
                self._safe_addstr(self.data_win, 1, 2, f"Display error: {str(e)}")
                self.data_win.refresh()
            except Exception:
                # If even this fails, just continue silently
                pass
    
    def print_scan_progress(self):
        """Print scan progress information."""
        try:
            if not ConfigManager.scan_thread:
                self._safe_addstr(self.data_win, 1, 2, "No active scan")
                return
                
            # Get scan statistics
            if not hasattr(ConfigManager.scan_thread, 'stats'):
                ConfigManager.scan_thread._scan_stats = {
                    "target": ConfigManager.target_info.get_host() if ConfigManager.target_info else "Unknown",
                    "start_time": time.time(),
                    "discovery_status": "Initializing",
                    "progress_percentage": 0,
                    "ports_found": len(ConfigManager.target_info.ports) if ConfigManager.target_info else 0,
                    "modules_total": 0,
                    "modules_running": 0,
                    "modules_pending": 0,
                    "modules_completed": 0,
                }
            stats = ConfigManager.scan_thread.stats
        except Exception as e:
            if self.data_win:
                self._safe_addstr(self.data_win, 1, 2, f"Error retrieving scan status: {str(e)}")
            return
        
        # Draw header
        self._safe_addstr(self.data_win, 1, 2, f"Scan Progress - {stats.get('target', 'Unknown Target')}", 
                          curses.color_pair(2) | curses.A_BOLD)
        
        # Draw status
        self._safe_addstr(self.data_win, 3, 2, f"Status: {stats.get('discovery_status', 'Unknown')}")
        
        # Draw elapsed time
        elapsed = stats.get('elapsed_time', 0)
        elapsed_formatted = self._format_time(elapsed)
        self._safe_addstr(self.data_win, 4, 2, f"Elapsed Time: {elapsed_formatted}")
        
        # Draw port count
        port_count = stats.get('total_ports', 0)
        self._safe_addstr(self.data_win, 5, 2, f"Discovered Ports: {port_count}")
        
        # Draw module statistics
        modules_total = stats.get('modules_total', 0)
        modules_completed = stats.get('modules_completed', 0)
        modules_running = stats.get('modules_running', 0)
        progress_percentage = stats.get('progress_percentage', 0)
        
        self._safe_addstr(self.data_win, 7, 2, f"Modules: {modules_completed}/{modules_total} completed, {modules_running} running")
        
        # Draw overall progress bar
        progress_width = self.width - 15
        self._safe_addstr(self.data_win, 9, 2, "Overall Progress: ")
        self._draw_progress_bar(self.data_win, 9, 19, progress_width, progress_percentage)
        self._safe_addstr(self.data_win, 9, 19 + progress_width + 1, f" {progress_percentage}%")
        
        # Draw running threads information
        self._safe_addstr(self.data_win, 11, 2, "Running Modules:", curses.color_pair(2) | curses.A_BOLD)
        
        try:
            # Get active threads
            active_tasks = [task for task_id, task in attack_thread_pool.tasks.items() 
                          if hasattr(task, 'status') and task.status.name == 'RUNNING']
            
            if active_tasks:
                for i, task in enumerate(active_tasks[:8]):  # Limit to 8 tasks to avoid overflow
                    module_name = task.module.name if hasattr(task, 'module') and task.module else "Unknown"
                    port = f"port {task.port}" if task.port else "target"
                    progress = f"{int(task.progress)}%" if hasattr(task, 'progress') else "..."
                    runtime = self._format_time(time.time() - task.start_time) if hasattr(task, 'start_time') else "..."
                    
                    self._safe_addstr(self.data_win, 12 + i, 4, f"• {module_name} ({port}) - {progress} - Running for {runtime}")
                    
                if len(active_tasks) > 8:
                    self._safe_addstr(self.data_win, 20, 4, f"... and {len(active_tasks) - 8} more")
            else:
                self._safe_addstr(self.data_win, 12, 4, "No active modules")
            
            # Draw completed module count
            y_offset = min(21, 12 + len(active_tasks) + 2)
            
            # Display recently completed tasks
            completed_tasks = [task for task_id, task in attack_thread_pool.tasks.items() 
                             if hasattr(task, 'status') and task.status.name == 'COMPLETED']
            
            self._safe_addstr(self.data_win, y_offset, 2, f"Recently Completed: {len(completed_tasks)}", curses.color_pair(2) | curses.A_BOLD)
            
            # Display the 5 most recently completed tasks
            sorted_completed = sorted(completed_tasks, key=lambda t: t.end_time if hasattr(t, 'end_time') else 0, reverse=True)
            for i, task in enumerate(sorted_completed[:5]):
                module_name = task.module.name if hasattr(task, 'module') else "Unknown"
                port = f"port {task.port}" if task.port else "target"
                
                self._safe_addstr(self.data_win, y_offset + 1 + i, 4, f"• {module_name} ({port})", curses.color_pair(3))
        except Exception as e:
            self._safe_addstr(self.data_win, 12, 4, f"Error displaying task info: {str(e)}")
    
    def print_data(self):
        """Print formatted port data in the data window."""
        try:
            if not ConfigManager.target_info:
                self._safe_addstr(self.data_win, 1, 2, "No target information available.")
                return
                
            data_unordered = ConfigManager.target_info.get_ports_dict_data()
            if not data_unordered:
                self._safe_addstr(self.data_win, 1, 2, "No port data available yet.")
                return

            # Draw header with host information
            host = ConfigManager.target_info.get_host()
            self._safe_addstr(self.data_win, 1, 2, f"Target: {host}", curses.color_pair(2) | curses.A_BOLD)
        except Exception as e:
            self._safe_addstr(self.data_win, 1, 2, f"Error displaying port data: {str(e)}")
            return
        
        # Calculate display area
        console_width = self.width - 4  # Margin
        custom_order = ["protocol", "product", "version", "modules"]
        data = {}

        # Format data based on custom order
        for key, value_dict in data_unordered.items():
            data[key] = {header: value_dict.get(header, "") for header in custom_order}

        headers = ["Port"] + [header.capitalize() for header in custom_order]
        index_width = 8
        column_widths = [index_width]
        
        # Calculate initial column widths
        for header in custom_order:
            header_width = len(header.capitalize())
            max_data_width = max(len(str(row.get(header, ""))) for row in data.values())
            column_widths.append(max(header_width, max_data_width))
        
        # Dynamically adjust column widths to fit the console width
        total_width = sum(column_widths) + (len(column_widths) - 1) * 3  # 3 for separator
        while total_width > console_width and min(column_widths) > 10:
            # Find the widest column and reduce its width
            max_width_index = column_widths.index(max(column_widths))
            column_widths[max_width_index] -= 1
            total_width = sum(column_widths) + (len(column_widths) - 1) * 3

        # Print headers with color
        y_offset = 3
        header_line = ""
        for i, header in enumerate(headers):
            header_text = header.center(column_widths[i])
            self._safe_addstr(self.data_win, y_offset, 2 + len(header_line), header_text, curses.color_pair(2) | curses.A_BOLD)
            header_line += header_text + " | " if i < len(headers) - 1 else header_text
        
        # Print separator line
        self._safe_addstr(self.data_win, y_offset + 1, 2, "-" * (total_width))

        # Print data rows
        y_offset += 2
        for i, (key, value) in enumerate(sorted(data.items(), key=lambda x: int(x[0]))):
            row_content = ""
            # Port column with color
            port_text = str(key).ljust(column_widths[0])
            self._safe_addstr(self.data_win, y_offset + i, 2, port_text, curses.color_pair(6) | curses.A_BOLD)
            row_content = port_text
            
            # Other columns
            for j, header in enumerate(custom_order):
                val = value.get(header, "")
                cell_text = truncate_value(str(val), column_widths[j+1]).ljust(column_widths[j+1])
                
                # Choose color based on content
                color = curses.color_pair(0)
                if header == "protocol" and val:
                    color = curses.color_pair(3) if val in ("http", "https", "ssh", "ftp") else curses.color_pair(0)
                    
                # Add separator and cell content
                self._safe_addstr(self.data_win, y_offset + i, 2 + len(row_content), " | ")
                row_content += " | "
                self._safe_addstr(self.data_win, y_offset + i, 2 + len(row_content), cell_text, color)
                row_content += cell_text
    
    def print_logs(self):
        """Print recent logs in the data window."""
        try:
            recent_logs = ConfigManager.get_logs()[-20:] if ConfigManager.get_logs() else []
            
            self._safe_addstr(self.data_win, 1, 2, "Recent Logs:", curses.color_pair(2) | curses.A_BOLD)
        
            for i, log in enumerate(recent_logs):
                color = curses.color_pair(0)
                if log.startswith("[-]"):
                    color = curses.color_pair(5)  # Error
                elif log.startswith("[+]"):
                    color = curses.color_pair(3)  # Success
                elif log.startswith("[!]"):
                    color = curses.color_pair(4)  # Warning
                elif log.startswith("[*]"):
                    color = curses.color_pair(6)  # Info
                    
                self._safe_addstr(self.data_win, 3 + i, 2, log, color)
        except Exception as e:
            self._safe_addstr(self.data_win, 1, 2, f"Error displaying logs: {str(e)}")
    
    def print_info(self, info_list: List[str]):
        """Print information in the data window."""
        try:
            for i, data in enumerate(info_list):
                # Detect headers (all caps or ending with ':')
                if data.isupper() or data.endswith(':') or '=' in data:
                    self._safe_addstr(self.data_win, 1 + i, 2, data, curses.color_pair(2) | curses.A_BOLD)
                else:
                    self._safe_addstr(self.data_win, 1 + i, 2, data)
        except Exception as e:
            self._safe_addstr(self.data_win, 1, 2, f"Error displaying info: {str(e)}")
    
    def _process_key(self, key: int, input_str: str) -> Tuple[str, bool]:
        """
        Process a key input.
        
        Args:
            key: Key code
            input_str: Current input string
            
        Returns:
            Tuple of (new_input_str, command_executed)
        """
        command_executed = False
        
        if key == curses.KEY_ENTER or key == 10 or key == 13:  # Enter key
            if input_str:
                self.command_processor.execute_command(input_str)
                command_executed = True
            input_str = ""
            
        elif key == curses.KEY_BACKSPACE or key == 127:  # Backspace
            input_str = input_str[:-1]
            
        elif key == 9:  # Tab key - cycle through modes
            if self._ui_mode == UIMode.PORT_DATA:
                self.switch_mode(UIMode.SCAN_PROGRESS)
            elif self._ui_mode == UIMode.SCAN_PROGRESS:
                self.switch_mode(UIMode.LOGS)
            elif self._ui_mode == UIMode.LOGS:
                self.switch_mode(UIMode.PORT_DATA)
                
        elif key == curses.KEY_F1:  # F1 - Help
            self.show_help()
            
        elif 32 <= key <= 126:  # Printable ASCII
            input_str += chr(key)
            
        return input_str, command_executed
    
    def _main_loop(self, stdscr):
        """Main interface loop handling user input and display."""
        self.stdscr = stdscr
        
        try:
            # Set up terminal
            curses.noecho()
            curses.cbreak()
            try:
                curses.curs_set(1)  # Show cursor
            except Exception as e:
                ConfigManager.log_warning(f"Terminal doesn't support cursor visibility control: {str(e)}")
                
            self.stdscr.nodelay(1)
            self.stdscr.keypad(True)  # Enable keypad for special keys
            self.stdscr.refresh()
            
            # Setup color pairs
            self._setup_colors()

            # Get terminal size and validate
            self.height, self.width = self.stdscr.getmaxyx()
            if self.height < 10 or self.width < 40:
                ConfigManager.log_warning(f"Terminal size too small: {self.width}x{self.height}, minimum 40x10 recommended")
            
            # Initialize windows
            self.data_win = curses.newwin(self.height - 2, self.width, 0, 0)
            self.status_win = curses.newwin(1, self.width, self.height - 2, 0)
            self.input_win = curses.newwin(1, self.width, self.height - 1, 0)
            self.input_win.keypad(True)
            self.input_win.nodelay(True)
            
            # Show help initially
            self.show_help()

            input_str = ""
            
            while True:
                # Handle window resize
                try:
                    new_height, new_width = self.stdscr.getmaxyx()
                    if new_height != self.height or new_width != self.width:
                        self.height, self.width = new_height, new_width
                        self.stdscr.clear()
                        self.data_win = curses.newwin(self.height - 2, self.width, 0, 0)
                        self.status_win = curses.newwin(1, self.width, self.height - 2, 0)
                        self.input_win = curses.newwin(1, self.width, self.height - 1, 0)
                        self.input_win.keypad(True)
                        self.input_win.nodelay(True)
                        self.stdscr.refresh()
                        self._last_update = 0  # Force update after resize
                except curses.error as e:
                    ConfigManager.log_error(f"Error resizing windows: {str(e)}")
                    
                # Update display
                self._update_display()
                self._draw_status_bar()
                
                # Process user input
                self.input_win.clear()
                prompt = "> "
                self.input_win.addstr(0, 0, prompt + input_str)
                try:
                    self.input_win.move(0, len(prompt) + len(input_str))  # Position cursor
                except curses.error:
                    pass
                self.input_win.refresh()
                
                try:
                    key = self.input_win.getch()
                    if key != -1:  # If a key was pressed
                        input_str, command_executed = self._process_key(key, input_str)
                        if command_executed:
                            self._last_update = 0  # Force update after command
                except curses.error:
                    pass
                    
                time.sleep(0.05)  # Small delay to prevent CPU hogging
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            # Ensure terminal is restored before logging
            try:
                curses.endwin()
            except Exception:
                pass
            ConfigManager.log_error(f"Fatal error in UI main loop: {str(e)}\n{error_trace}")
