import threading
import subprocess
import os
from attackThread import AttackThread
from utils import *
import nmap

def nikto(protocol,hostname, port):
    nikto = AttackThread(f"nikto_{port}", port, ["/usr/bin/nikto", "--url", f"{protocol}://{hostname}:{port}"])
    nikto.start()
    return nikto

def wfuzz_sub_brute(protocol,hostname,port):
    fuzz_hide_cmd = f'echo "www" | wfuzz -c -z stdin -H "Host:FUZZ.{hostname}" -u {protocol}://{hostname}:{port} 2>/dev/null | grep -oP "\b[0-9]+(?=\sCh\b)"'
    fuzz_hide_value=str(os.system(fuzz_hide_cmd))
    sub_brute = AttackThread(f"WFUZZ_Sub_Brute_{port}", port, ["/usr/bin/wfuzz", "-u", f"{protocol}://{hostname}:{port}","-c","-w","/usr/share/seclists/Discovery/DNS/subdomains-top1million-20000.txt","-H",f"Host:FUZZ.{hostname}","--hh",fuzz_hide_value])
    sub_brute.start()
    return sub_brute

def feroxbuster(protocol,hostname,port):
    feroxbuster = AttackThread(
        f"feroxbuster_{port}", port, ["/usr/bin/feroxbuster",
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
    cmsScan = AttackThread(f"cmsScan_{port}", port, f"/usr/bin/python /home/kali/tools/CMSeeK/cmseek.py -u {protocol}://{hostname}:{port} --batch -r")
    cmsScan.start()
    return cmsScan


def crawl_web_data(protocol,hostname,port):
    # Daten von der Webseite holen
    response = requests.get(f"{protocol}://{hostname}:{port}")
    content = response.text

    # Reguläre Ausdrücke für die gewünschten Informationen
    hostname_pattern = re.compile(r'https?://([A-Za-z0-9.-]+)')
    email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
    software_version_pattern = re.compile(r'([a-zA-Z\s0-9_-]+)\s*v?\d+\.\d+(\.\d+)?')
    url_pattern = re.compile(r'https?://[^\s<>"]+|www\.[^\s<>"]+')

    # Informationen extrahieren
    hostnames = list(set(hostname_pattern.findall(content)))
    emails = list(set(email_pattern.findall(content)))
    software_versions = list(set(software_version_pattern.findall(content)))
    urls = list(set(url_pattern.findall(content)))

    return {
        'hostnames': hostnames,
        'emails': emails,
        'software_versions': [software[0] for software in software_versions],
        'urls': urls
    }
#    crawl_web = AttackThread("crawl_web_data",port,f"modules/crawl_web_data.py {protocol}://{hostname}:{port}")
#    crawl_web.start()
#    return crawl_web

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
                'product': nm[host]['tcp'][port]['product']
            }
            port_info['protocol'] = check_protocol(ip, str(port))
            port_info["modules"] = []
            port_info["info"] = {}
            scan_res[str(port)] = port_info
    return scan_res
