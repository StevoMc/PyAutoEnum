"""Command processor for the PyAutoEnum UI."""

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
            # Add more commands here as needed
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
            ConfigManager.log_info(f"Help for {cmd}:")
            # Add specific help text for commands as needed
        else:
            ConfigManager.log_info("Available commands: " + ", ".join(self.commands.keys()))
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
        display_data.append(f"Information about port [{port}]")

        for key, value in port_data.to_dict().items():
            display_data.append(f"{key}: {value}")

        ConfigManager.log_info(f"Showing details for port {port}")
        ConfigManager.display_data = display_data

    def command_back(self, args: List[str]) -> None:
        """
        Return to the main view.
        
        Args:
            args: Command arguments
        """
        ConfigManager.display_data = []
