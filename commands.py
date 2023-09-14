import threading
import traceback
from utils import log_interaction, log_info, log_error, get_console_width, truncate_value

prompt_lock = threading.Lock()

def command_help(cmd=None):
    if cmd:
        log_info(f"help {cmd} called")
    else: log_info("help")


def command_show(args):
    if len(args) == 0:
        log_interaction("Useage: show {port}")
        return
    port = args[0]

    from scan import open_ports, set_display_data
    ddata = []
    ddata.append(f"Information about port [{port}]")

    console_width = get_console_width()
    for key, value in open_ports[port].items():
#        data = truncate_value(f"{key}: {value}",console_width)
        ddata.append(f"{key}: {value}")
    set_display_data(ddata)


def command_back(args):
    from scan import set_display_data
    set_display_data([])


def execute_command(user_input):
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
        except: log_error(f"Error in execution of command '{command}' with args '{args}':\n{traceback.format_exc()}")
    else:
        log_interaction("Command not found. Use 'help' to list commands")


# Define a dictionary to map commands to functions or actions
command_dict = {
    "help": command_help,
    "show": command_show,
    "back": command_back
}
