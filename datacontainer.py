import yaml

def get_display_data():
    global display_data
    return display_data

def set_display_data(data):
    global display_data
    display_data = data
def set_working_dir(wd):
    global path
    path = wd

def get_working_dir():
    return path

def load_modules(file_path):
    with open(file_path, 'r') as yaml_file:
        return yaml.safe_load(yaml_file)["attacks"]

def get_modules():
    return modules


path = ""
modules = load_modules("modules.yml")
display_data = None

