from attacks import *
from utils import *
import argparse
from bs4 import BeautifulSoup
import threading
from os import getlogin

tasks = []
open_ports = {}
open_ports_lock = threading.Lock()
path = ""
command=""

def start_scan(target, open_ports_save):
    global open_ports
    if open_ports_save:
        with open_ports_lock:
            open_ports=open_ports_save

    write_log(f"Attack started for {target}:")
    if check_target_up(target)==False:
        write_log(f"[-] Error: No Connection to {target}")
        exit()
    else: write_log("[+] Target is up")

    if not open_ports:
        open_ports_min = check_open_ports(target,f"-F -T4")
        with open_ports_lock:
            open_ports = merge_dicts(open_ports,open_ports_min)

    # Webserver
    http_ports = filter_dict_by_values(open_ports, "protocol", ["http","https"])
    for port in http_ports:
        scan_webserver(target, port, http_ports[port])

    if not os.path.exists(f"{path}full.nmap"):
        full_scan = check_open_ports(target,f"-p- -sV -oN {path}full.nmap")
        with open_ports_lock:
            open_ports = merge_dicts(open_ports,full_scan)
        write_log(f"[+] Completed: Full Nmap")


def scan_webserver(target, port, values):
    global tasks
    protocol = values["protocol"]
    hostname = get_hostname(target, port, protocol)

    #Get HTML Title
    response = requests.get(f"{protocol}://{hostname}:{port}")
    soup = BeautifulSoup(response.text, 'html.parser')
    open_ports[port]["info"]["title"] = soup.title

    #Crawl Web Data
    write_log(f"[+] Started Attack: Crawl Web Data [{port}]")
    crawled_data = crawl_web_data(protocol,hostname,port)
    for hostname in crawled_data["hostnames"]:
        process_new_hostname(hostname)

    #Start Sub Domain Brute
    if hostname != target:
        tasks.append(wfuzz_sub_brute(protocol,hostname,port))

    #Start Feroxbuster Dir Bruteforce
    write_log(f"[+] Started Attack: feroxbuster [{port}]")
    tasks.append(feroxbuster(protocol,hostname,port))

    #Start Nikto Web Analyser
    write_log(f"[+] Started Attack: nikto [{port}]")
    tasks.append(nikto(protocol,hostname, port))

    #CMS Scan
    write_log(f"[+] Started Attack: cmsScan [{port}]")
    tasks.append(cmsScan(protocol,hostname,port))


def get_data():
    return open_ports

def set_working_dir(wd):
    global path
    path = wd
    AttackThread.path = wd

def get_working_dir():
    return path

def send_command(cmd):
   global command
   command = cmd
   write_log(f"[<{os.getlogin()}>] {command}")

def get_command():
    return command

def complete_module(name,port):
    with open_ports_lock:
        open_ports[port]["modules"].append(name)
