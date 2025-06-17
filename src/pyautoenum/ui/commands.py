"""Command processor for the PyAutoEnum UI."""

import sys
import threading
import traceback
from typing import List

from pyautoenum.config.manager import ConfigManager


class CommandProcessor:
    """
    Processes and executes commands entered in the UI.
    """
    
    def __init__(self):
        """Initialize command processor with available commands."""
        self.commands = {
            "help": self.command_help,
            "show": self.command_show,
            "back": self.command_back,
            "quit": self.command_quit,
            "exit": self.command_quit,
            "clear": self.command_clear,
            "logs": self.command_logs,
            "scan": self.command_scan,
            "ports": self.command_ports,
        }
        
    def execute_command(self, user_input: str) -> None:
        """
        Execute a command from user input.
        
        Args:
            user_input: Command string from the user
        """
        ConfigManager.log_interaction(user_input)

        # Split the user input into tokens
        tokens = user_input.split()

        # Check if empty
        if not tokens:
            return

        # Extract the command and arguments
        command = tokens[0].lower()
        args = tokens[1:]

        # Check if the command exists in the dictionary
        if command in self.commands:
            try:
                self.commands[command](args)
            except Exception:
                ConfigManager.log_error(
                    f"Error in execution of command '{command}' with args '{args}':\n{traceback.format_exc()}"
                )
        else:
            ConfigManager.log_interaction("Command not found. Use 'help' to list commands")

    def command_help(self, args: List[str]) -> None:
        """
        Display help information.
        
        Args:
            args: Command arguments
        """
        if args:
            cmd = args[0]
            help_text = []
            help_text.append(f"Help for '{cmd}':")
            
            if cmd == "show":
                help_text.append("Usage: show [port]")
                help_text.append("Shows detailed information about a specific port")
            elif cmd == "back":
                help_text.append("Usage: back")
                help_text.append("Returns to the main view")
            elif cmd == "quit" or cmd == "exit":
                help_text.append("Usage: quit or exit")
                help_text.append("Exits the application")
            elif cmd == "clear":
                help_text.append("Usage: clear")
                help_text.append("Clears the screen")
            elif cmd == "logs":
                help_text.append("Usage: logs")
                help_text.append("Shows recent log messages")
            elif cmd == "scan":
                help_text.append("Usage: scan")
                help_text.append("Shows the current scan progress")
            elif cmd == "ports":
                help_text.append("Usage: ports")
                help_text.append("Shows discovered ports and services")
            else:
                help_text.append(f"No specific help available for '{cmd}'")
                
            if ConfigManager.ui_interface:
                ConfigManager.ui_interface.set_info_data(help_text)
            else:
                ConfigManager.log_info("\n".join(help_text))
        else:
            # Show general help
            if ConfigManager.ui_interface:
                ConfigManager.ui_interface.show_help()
            else:
                commands_list = ", ".join(sorted(self.commands.keys()))
                ConfigManager.log_info(f"Available commands: {commands_list}")
                ConfigManager.log_info("Use 'help <command>' for more information on a specific command")

    def command_show(self, args: List[str]) -> None:
        """
        Show detailed information about a port.
        
        Args:
            args: Command arguments
        """
        if not args:
            ConfigManager.log_interaction("Usage: show [port]")
            return

        if not ConfigManager.target_info:
            ConfigManager.log_error("No target information available")
            return

        port = args[0]
        port_data = ConfigManager.target_info.get_port(port)
        
        if not port_data:
            ConfigManager.log_error(f"No information available for port {port}")
            return
            
        display_data = []
        display_data.append(f"PORT {port} DETAILS")
        display_data.append("=" * 30)

        # Show basic port info
        display_data.append(f"Protocol: {port_data.protocol}")
        display_data.append(f"Service: {port_data.product}")
        display_data.append(f"Version: {port_data.version}")
        
        # Show hostnames if available
        if port_data.hostnames:
            display_data.append("\nHostnames:")
            for hostname in port_data.hostnames:
                display_data.append(f"  - {hostname}")
        
        # Show modules run
        if port_data.modules:
            display_data.append("\nModules Run:")
            for module in sorted(port_data.modules):
                display_data.append(f"  - {module}")
                
        # Show additional info
        if port_data.infos:
            display_data.append("\nAdditional Information:")
            for key, value in sorted(port_data.infos.items()):
                display_data.append(f"  {key}: {value}")

        if ConfigManager.ui_interface:
            ConfigManager.ui_interface.set_info_data(display_data)
        else:
            ConfigManager.display_data = display_data
            ConfigManager.log_info(f"Showing details for port {port}")

    def command_back(self, args: List[str]) -> None:
        """
        Return to the main view.
        
        Args:
            args: Command arguments
        """
        if ConfigManager.ui_interface:
            ConfigManager.ui_interface.switch_mode("port_data")
        ConfigManager.display_data = []
        
    def command_quit(self, args: List[str]) -> None:
        """
        Exit the application.
        
        Args:
            args: Command arguments
        """
        ConfigManager.log_info("Exiting PyAutoEnum")
        
        # Stop any active scan
        if ConfigManager.scan_thread:
            ConfigManager.scan_thread.stop()
            
        # Give threads a moment to clean up
        threading.Timer(0.5, lambda: sys.exit(0)).start()
        
    def command_clear(self, args: List[str]) -> None:
        """
        Clear the screen.
        
        Args:
            args: Command arguments
        """
        if ConfigManager.ui_interface:
            ConfigManager.ui_interface.switch_mode("port_data")
        ConfigManager.display_data = []
        ConfigManager.log_info("Screen cleared")
        
    def command_logs(self, args: List[str]) -> None:
        """
        Show logs.
        
        Args:
            args: Command arguments
        """
        if ConfigManager.ui_interface:
            ConfigManager.ui_interface.switch_mode("logs")
        ConfigManager.log_info("Showing logs")
        
    def command_scan(self, args: List[str]) -> None:
        """
        Show scan progress.
        
        Args:
            args: Command arguments
        """
        if ConfigManager.ui_interface:
            ConfigManager.ui_interface.switch_mode("scan_progress")
        
        if not ConfigManager.scan_thread:
            ConfigManager.log_warning("No active scan")
        else:
            ConfigManager.log_info("Showing scan progress")
            
    def command_ports(self, args: List[str]) -> None:
        """
        Show discovered ports.
        
        Args:
            args: Command arguments
        """
        if ConfigManager.ui_interface:
            ConfigManager.ui_interface.switch_mode("port_data")
        
        if not ConfigManager.target_info or not ConfigManager.target_info.ports:
            ConfigManager.log_warning("No ports discovered yet")
        else:
            ConfigManager.log_info(f"Showing {len(ConfigManager.target_info.ports)} discovered ports")
