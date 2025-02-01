from pathlib import Path
from attacks import *
import threading
from ui.commands import execute_command, prompt_lock
from analyse import *
from core.utils import *
from core.config import *
from core.attack_thread import AttackThread

open_ports = {}
open_ports_lock = threading.Lock()
command=""

def start_scan(target, ports, open_ports_save):
    target = get_hostname_from_url(target)
    
    global open_ports
    if open_ports_save:
        with open_ports_lock:
            open_ports=open_ports_save

    log_info(f"Starting Enum for {target}:")
    if check_target_up(target)==False:
        log_warning(f"Target  {target} DID NOT respond to PING")        
    else: log_success("Target is up")

    if not open_ports:
        nmap_ports = f"-p {ports}" if ports else "-F"
        log_info(f"Started Fast NMAP Scan (-Pn {nmap_ports} -T4)")
        open_ports_min = check_open_ports(target, f"-Pn {nmap_ports} -T4")                 
        with open_ports_lock:
            open_ports = merge_dicts(open_ports,open_ports_min)

    if "445" in open_ports:
        AttackThread("smb_enum_anon","445",enum_smb, command_args=[target],analyse=analyse_smb_enum_anon).start()
        
    nmap_ports = f"-p {ports}" if ports else "-p-"
    
    # Start the AttackThread with the updated path handling
    AttackThread(
        f"Nmap Version Scan",
        "0",
        command=check_open_ports,
        command_args=[target, f"-Pn {nmap_ports} -sV -oN [path]"],  # Use Path for the output file
        analyse=analyse_full_nmap
    ).start()

    # Webserver
    http_ports = {k: v for k, v in open_ports.items() if v.get('hostnames',None) is not None}
    #For every http port
    for port in http_ports:
        # for every hostname of port
        for i in range(len(http_ports[port]["hostnames"])):
            hostname = http_ports[port]["hostnames"][i][0]
            protocol = http_ports[port]["hostnames"][i][1]
            scan_webserver(hostname, port, protocol)

def scan_webserver(hostname, port, protocol):
    global tasks

    #Crawl Web Data
    # log_info(f"Started Enum: Crawl Web Data [{hostname} {port}]")
    # try:
    #     crawled_data = crawl_web_data(protocol,hostname,port)

    #     #Add hostnames
    #     for hostname in crawled_data["hostnames"]:
    #         if hostname not in [hosts_data[0] for hosts_data in open_ports[port]["hostnames"]]:
    #             if process_new_hostname(hostname):
    #                 with open_ports_lock:
    #                     if check_http_connection("http",hostname,port):
    #                         open_ports[port]["hostnames"].append(hostname)
    #     add_information(port, "info", crawled_data)
    #     log_info(f"Finished Enum: Crawl Web Data [{hostname} {port}]")

    # except Exception as e:
    #     log_warning(f"Could not crawl website: {e}")


    #TODO
    # Crawl Daten analysieren
    # wenn seite zu klein -> mögliche hostnamen und gefundene urls probieren
    # wenn keine gefunden, alles an
    
    start_attack_modules(hostname, port, protocol)

def start_attack_modules(hostname: str, port: int, protocol: str):
    """Starts attack modules based on the given hostname, port, and protocol."""    

    for attack in Config.modules:
        name = attack.get('name')
        command = attack.get('command')
        switches = attack.get('switches', [])
        module_protocols = attack.get('protocol', [])
        analyse_function = attack.get('analyse_function')

        if protocol in module_protocols:
            # Replace placeholders in switches with actual values
            formatted_switches = []
            for switch in switches:
                formatted_switches.append(
                    switch.replace("[protocol]", protocol)
                    .replace("[hostname]", hostname)
                    .replace("[port]", str(port))
                )

            # Construct the full command
            command_args = [command] + formatted_switches
            
            # Start the attack thread
            try:
                log_info(f"Starting attack module: {name} on {protocol}://{hostname}:{port}")
                AttackThread(
                    name=name,
                    port=port,
                    command=command,
                    command_args=command_args,
                    analyse=analyse_function
                ).start()
            except Exception as e:
                log_error(f"Failed to start attack module {name}: {str(e)}")


def get_data():
    return open_ports

def send_command(cmd):
    global command
    command = cmd    
    if command != "":
        with prompt_lock:
            execute_command(command)
    command = ""


def get_command():
    return command

def complete_module(name,port):
    with open_ports_lock:
        if open_ports and port in open_ports.keys():           
            open_ports[port]["modules"].append(name)

def check_module_finished(name, port):
    with open_ports_lock:
        if open_ports and port in open_ports.keys():            
            return name in open_ports[port]["modules"]
        else: return False

def add_information(port,column,info):
    with open_ports_lock:
        if column in open_ports[port]:
            current_value = open_ports[port][column]

            if isinstance(current_value, dict) and isinstance(info, dict):
                current_value.update(info)
            elif isinstance(current_value, list) and isinstance(info, list):
                current_value.extend(info)
            elif isinstance(current_value, list):
                current_value.append(info)
            else:
                raise ValueError(f"Key '{column}' already exists for port '{port}' and is not compatible with provided info.")
        else:
            open_ports[port][column] = info 
            
        

def override_open_ports(dict):
    global open_ports
    open_ports = dict


class ScanThread (threading.Thread):
    def __init__(self, target, ports, open_ports_save):
        threading.Thread.__init__(self)
        self.target= target
        self.open_ports_save = open_ports_save
        self.finished = False
        self.daemon = True
        self.ports = ports

    def run(self):
        try:
            start_scan(self.target, self.ports, self.open_ports_save)
            self.finished = True
        except: 
            stack_trace_str = traceback.format_exc()
            log_error(f"Exception in scanThread: {stack_trace_str}")