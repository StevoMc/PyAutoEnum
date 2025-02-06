import threading
import traceback
from core.config import Config

prompt_lock = threading.Lock()


command = ""
def send_command(cmd):
    """Executes a command via the UI."""
    global command
    command = cmd    
    if command:
        with prompt_lock:
            execute_command(command)
    command = ""

def get_command():
    """Returns the last issued command."""
    return command

def command_help(cmd=None):
    if cmd:
        Config.log_info(f"help {cmd} called")
    else: Config.log_info('Commands: '+", ".join(command_dict.keys()))


def command_show(args):
    if len(args) == 0:
        Config.log_interaction("Useage: show [port]")
        return
    
    port = args[0]
    ddata = []
    ddata.append(f"Information about port [{port}]")

    for key, value in Config.target_info.get_port(port).to_dict().items():
        ddata.append(f"{key}: {value}")
        
    Config.log_info(ddata)
    Config.display_data = ddata


def command_back(args):
    Config.display_data =[]


def execute_command(user_input):
    Config.log_interaction(user_input)
    
    # Split the user input into tokens
    tokens = user_input.split()

    #Check if empty
    if len(tokens) == 0: return

    # Extract the command and arguments
    command = tokens[0].lower()
    args = tokens[1:]

    # Check if the command exists in the dictionary
    if command in command_dict:
        try: result = command_dict[command](args)
        except: Config.log_error(f"Error in execution of command '{command}' with args '{args}':\n{traceback.format_exc()}")
    else:
        Config.log_interaction("Command not found. Use 'help' to list commands")


# Define a dictionary to map commands to functions or actions
command_dict = {
    "help": command_help,
    "show": command_show,
    "back": command_back
}
