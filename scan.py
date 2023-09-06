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
    http_ports = {k: v for k, v in open_ports.items() if v.get('hostnames',None) is not None}
    #For every http port
    for port in http_ports:
        # for every hostname of port
        for i in range(len(http_ports[port]["hostnames"])):
            hostname = http_ports[port]["hostnames"][i][0]
            protocol = http_ports[port]["hostnames"][i][1]
            scan_webserver(target, port,hostname, protocol)

    if not os.path.exists(f"{path}full.nmap"):
        full_scan = check_open_ports(target,f"-p- -sV -oN {path}full.nmap")
        with open_ports_lock:
            open_ports = merge_dicts(open_ports,full_scan)
        write_log(f"[+] Completed: Full Nmap")


def scan_webserver(target, port, hostname, protocol):
    global tasks

    #Crawl Web Data
    write_log(f"[+] Started Attack: Crawl Web Data [{hostname} {port}]")
    crawled_data = crawl_web_data(protocol,hostname,port)
    for hostname in crawled_data["hostnames"]:
        write_log([hosts_data[0] for hosts_data in open_ports[port]["hostnames"]])
        if hostname not in [hosts_data[0] for hosts_data in open_ports[port]["hostnames"]]:
            if process_new_hostname(hostname):
                with open_ports_lock:
                    if check_http_connection("http",hostname,port):
                        open_ports[port]["hostnames"].append(hostname)

    #TODO
    # Crawl Daten analysieren
    # wenn seite zu klein -> mögliche hostnamen und gefundene urls probieren
    # wenn keine gefunden, alles an

    #Start Sub Domain Brute
    if hostname != target:
        tasks.append(wfuzz_sub_brute(protocol,hostname,port))

    #Start Feroxbuster Dir Bruteforce
    tasks.append(feroxbuster(protocol,hostname,port))

    #Start Nikto Web Analyser
    tasks.append(nikto(protocol,hostname, port))

    #CMS Scan
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

def check_module_finished(name, port):
    with open_ports_lock:
        return name in open_ports[port]["modules"]
