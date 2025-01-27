from attacks import *
from utils import *
import argparse
from bs4 import BeautifulSoup
import threading
from os import getlogin
from commands import execute_command, prompt_lock
from analyse import *
from datacontainer import *

open_ports = {}
open_ports_lock = threading.Lock()
command=""

def start_scan(target, open_ports_save):
    if get_modules():
        log_success(f"{len(get_modules())} modules loaded")

    global open_ports
    if open_ports_save:
        with open_ports_lock:
            open_ports=open_ports_save

    log_info(f"Starting Enum for {target}:")
    if check_target_up(target)==False:
        log_error(f"Error: No Connection to {target}")
        exit()
    else: log_success("Target is up")

    if not open_ports:
        open_ports_min = check_open_ports(target,f"-F -T4")
        with open_ports_lock:
            open_ports = merge_dicts(open_ports,open_ports_min)

    if "445" in open_ports:
        AttackThread("smb_enum_anon","445",enum_smb, command_args=[target],analyse=analyse_smb_enum_anon).start()
    path = get_working_dir()
    AttackThread("full_nmap","0",check_open_ports, command_args=[target,f"-p- -sV -oN {path}full.nmap"], analyse=analyse_full_nmap).start()

    # Webserver
    http_ports = {k: v for k, v in open_ports.items() if v.get('hostnames',None) is not None}
    #For every http port
    for port in http_ports:
        # for every hostname of port
        for i in range(len(http_ports[port]["hostnames"])):
            hostname = http_ports[port]["hostnames"][i][0]
            protocol = http_ports[port]["hostnames"][i][1]
            scan_webserver(target, port,hostname, protocol)

def scan_webserver(target, port, hostname, protocol):
    global tasks

    #Crawl Web Data
    log_info(f"Started Enum: Crawl Web Data [{hostname} {port}]")
    try:
        crawled_data = crawl_web_data(protocol,hostname,port)

        #Add hostnames
        for hostname in crawled_data["hostnames"]:
            if hostname not in [hosts_data[0] for hosts_data in open_ports[port]["hostnames"]]:
                if process_new_hostname(hostname):
                    with open_ports_lock:
                        if check_http_connection("http",hostname,port):
                            open_ports[port]["hostnames"].append(hostname)
        add_information(port, "info", crawled_data)
        log_info(f"Finished Enum: Crawl Web Data [{hostname} {port}]")

    except Exception as e:
        log_warning(f"Could not crawl website: {e}")


    #TODO
    # Crawl Daten analysieren
    # wenn seite zu klein -> mögliche hostnamen und gefundene urls probieren
    # wenn keine gefunden, alles an

    #Start Sub Domain Brute
    AttackThread("wfuzz_sub_brute",port, wfuzz_sub_brute, command_args=[protocol,hostname,port], analyse=analyse_wfuzz_sub_brute).start()

    #Start Feroxbuster Dir Bruteforce
#   feroxbuster(protocol,hostname,port)

    #Start Nikto Web Analyser
    nikto(protocol,hostname, port)

    #CMS Scan
    cmsScan(protocol,hostname,port)

    # WhatWeb scann
    whatWebScan(protocol,hostname,port)


def get_data():
    return open_ports

def send_command(cmd):
    global command
    command = cmd
    log_interaction(f"[<{os.getlogin()}>] {command}")
    if command != "":
        with prompt_lock:
            execute_command(command)
    command = ""


def get_command():
    return command

def complete_module(name,port):
    with open_ports_lock:
        open_ports[port]["modules"].append(name)

def check_module_finished(name, port):
    with open_ports_lock:
        return name in open_ports[port]["modules"]

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
