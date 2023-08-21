from attacks import *
from utils import *
from attackThread import AttackThread as at
import argparse
import re
import socket
import time
import nmap
from bs4 import BeautifulSoup

tasks = []
open_ports = []


def start_scan(target):
    global open_ports
    write_log(f"Attack started for {target}:")
    if check_target_up(target)==False:
        write_log(f"[-] Error: No Connection to {target}")
        exit()
    else: write_log("[+] Target is up")
    open_ports = check_open_ports(target,f"-F -T4")

    # Webserver
    http_ports = filter_dict_by_values(open_ports, "protocol", ["http","https"])
    for port in http_ports:
        scan_webserver(target, port, http_ports[port])

    write_log("ScanThreadFinished")
    #open_ports = check_open_ports(target,f"-p- -sV -oN {at.path}full.nmap")
    #Print Ports
    #print_data(open_ports)

def scan_webserver(target, port, values):
    global tasks
    protocol = values["protocol"]
    hostname = get_hostname(target, port, protocol)

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

    response = requests.get(f"{protocol}://{hostname}:{port}")
    soup = BeautifulSoup(response.text, 'html.parser')
    open_ports[port]["info"]["title"] = soup.title


def check_open_ports(ip,args):
    write_log(f"[+] Nmap Port Scan: {args}")
    nm = nmap.PortScanner()
    nm.scan(ip, arguments=args)
    scan_res ={}
    for host in nm.all_hosts():
        for port in nm[host]['tcp']:
            port_info = {
                'service': nm[host]['tcp'][port]['name'],
                'version': nm[host]['tcp'][port]['version']
            }
            port_info['protocol'] = check_protocol(ip, str(port))
            port_info["modules"] = []
            port_info["info"] = {}
            scan_res[int(port)] = port_info
    return scan_res

def get_data():
    return open_ports

def stop_tasks():
    global tasks
    for task in tasks:
        task.stop()
    tasks = []
