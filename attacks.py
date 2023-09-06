import threading
import subprocess
import os
from attackThread import AttackThread
from utils import *
import nmap

def nikto(protocol,hostname, port):
    nikto = AttackThread(f"nikto_{hostname}_{port}", port, ["/usr/bin/nikto", "--url", f"{protocol}://{hostname}:{port}"])
    nikto.start()
    return nikto

def wfuzz_sub_brute(protocol,hostname,port):
    fuzz_hide_cmd = f'echo "www" | wfuzz -c -z stdin -H "Host:FUZZ.{hostname}" -u {protocol}://{hostname}:{port} 2>/dev/null | grep -oP "\b[0-9]+(?=\sCh\b)"'
    fuzz_hide_value=str(os.system(fuzz_hide_cmd))
    sub_brute = AttackThread(f"WFUZZ_Sub_Brute_{hostname}_{port}", port, ["/usr/bin/wfuzz", "-u", f"{protocol}://{hostname}:{port}","-c","-w","/usr/share/seclists/Discovery/DNS/subdomains-top1million-20000.txt","-H",f"Host:FUZZ.{hostname}","--hh",fuzz_hide_value])
    sub_brute.start()
    return sub_brute

def feroxbuster(protocol,hostname,port):
    feroxbuster = AttackThread(
        f"feroxbuster_{hostname}_{port}", port, ["/usr/bin/feroxbuster",
                        "-u",
                        f"{protocol}://{hostname}:{port}/",
                        "-A",
                        "-E",
                        "--no-state",
                        "--smart",
                        "--threads",
                        "150",
                        "-C",
                        "404",
                        "-w", "/usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt"])
    feroxbuster.start()
    return feroxbuster


def cmsScan(protocol,hostname,port):
    cmsScan = AttackThread(f"cmsScan_{hostname}_{port}", port, f"/usr/bin/python /home/kali/tools/CMSeeK/cmseek.py -u {protocol}://{hostname}:{port} --batch -r")
    cmsScan.start()
    return cmsScan


def crawl_web_data(protocol,hostname,port):
    response = requests.get(f"{protocol}://{hostname}:{port}")
    content = response.text

    hostname_pattern = re.compile(r'https?://([A-Za-z0-9.-]+)')
    email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
    software_version_pattern = re.compile(r'([a-zA-Z\s0-9_-]+)\s*v?\d+\.\d+(\.\d+)?')
    url_pattern = re.compile(r'https?://[^\s<>"]+|www\.[^\s<>"]+')
    software_versions = list(set(software_version_pattern.findall(content)))


    hostnames = list(set(hostname_pattern.findall(content)))
    hostnames_checked = []
    for hostname_test in hostnames:
        try:
            if socket.gethostbyname(hostname) == socket.gethostbyname(hostname_test):
                if hostname_test not in hostnames_checked:
                    hostnames_checked.append(hostname_test)
        except socket.gaierror:
            pass

    return {
        'title':response.content.title,
        'hostnames': hostnames_checked,
        'emails': list(set(email_pattern.findall(content))),
        'software_versions': [software[0] for software in software_versions],
        'urls': list(set(url_pattern.findall(content))),
        'size': len(response.content),
        'content':content
    }

def check_open_ports(ip,args):
    write_log(f"[+] Nmap Port Scan: {args}")
    nm = nmap.PortScanner()
    nm.scan(ip, arguments=args)
    scan_res ={}
    for host in nm.all_hosts():
        for port in nm[host]['tcp']:
            port_info = {
                'service': nm[host]['tcp'][port]['name'],
                'version': nm[host]['tcp'][port]['version'],
                'product': nm[host]['tcp'][port]['product'],
             'hostnames' : get_hostnames(ip, str(port)),
                "modules": [],
                   "info":{}
            }
            scan_res[str(port)] = port_info
    return scan_res
