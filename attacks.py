import threading
import subprocess
import os
from attackThread import AttackThread
from utils import *
from smb_utils import *
from utils import *
from analyse import *
import nmap
from bs4 import BeautifulSoup
import concurrent.futures


def nikto(protocol,hostname, port):
    AttackThread(f"nikto_{hostname}_{port}", port, ["/usr/bin/nikto", "--url", f"{protocol}://{hostname}:{port}"]).start()


def wfuzz_sub_brute(protocol,hostname,port, threads=500):
    url = f"{protocol}://{hostname}:{port}"
    wordlist = "/usr/share/seclists/Discovery/DNS/subdomains-top1million-20000.txt"

    def get_chars_for_subdomain(subdomain,rec_level=0):
        try:
            return len(requests.get(url, headers={"Host":f"{subdomain.strip()}.{hostname}"},timeout=2+rec_level, verify=False, allow_redirects=False).text)
        except:
            if rec_level:
                time.sleep(rec_level)
            if rec_level<=3:
                rec_level+=1
                return get_chars_for_subdomain(subdomain,rec_level)
            else:
                print("{rec_level} times connection error {subdomain}")
                return 0


    response_www_value = get_chars_for_subdomain("www")

    with open(wordlist) as list:
        subs = list.readlines()

    count = 0
    found_subdomains = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
        futures = {executor.submit(get_chars_for_subdomain,subdomain.strip()): subdomain for subdomain in subs if subdomain[0] != "#"}
        for future in concurrent.futures.as_completed(futures):
            sub = futures[future]
            if future.result() != response_www_value:
                found_subdomains.append([f"{sub.strip()}.{hostname}",protocol])
    return {str(port):found_subdomains}


def feroxbuster(protocol,hostname,port):
    AttackThread(
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
                        "-w", "/usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt"]).start()


def cmsScan(protocol,hostname,port):
    AttackThread(f"cmsScan_{hostname}_{port}", port, f"/usr/bin/python /home/kali/tools/CMSeeK/cmseek.py -u {protocol}://{hostname}:{port} --batch -r").start()

def whatWebScan(protocol,hostname,port):
    AttackThread(f"whatWebScan_{hostname}_{port}", port, f"whatweb {protocol}://{hostname}:{port}").start()



def crawl_web_data(protocol,hostname,port):
    response = requests.get(f"{protocol}://{hostname}:{port}")
    content = response.text
#    soup = BeautifulSoup(content, 'html.parser')

    hostname_pattern = re.compile(r'https?://([A-Za-z0-9.-]+)')
    email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
    software_version_pattern = re.compile(r'([a-zA-Z\s0-9_-]+)\s*v?\d+\.\d+(\.\d+)?')
    url_pattern = re.compile(r'https?://[^\s<>"]+|www\.[^\s<>"]+')
    software_versions = list(set(software_version_pattern.findall(content)))
 #   default_page = is_default_page(reponse)

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
#        'title':soup.title,
        'hostnames': hostnames_checked,
        'emails': list(set(email_pattern.findall(content))),
        'software_versions': [software[0] for software in software_versions],
        'urls': list(set(url_pattern.findall(content))),
        'size': len(response.content),
#        'default_page':default_page,
        'content':content
    }

def check_open_ports(ip,args):
    nm = nmap.PortScanner()
    nm.scan(ip, arguments=args)
    scan_res ={"0":{"modules":[]}}
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


def enum_smb(ip, username="", password=""):
    conn = SMBConnection(username, password, "", str(ip))
    assert conn.connect(str(ip), 445)

    smb_shares = get_smb_shares(conn)

    for share_name,smb_share in smb_shares.items():
        if smb_share['readable'] or smb_share['writeable']:
            log_info(f"Found smb share {share_name} read:{smb_share['readable']} write:{smb_share['writeable']}")

    download_files_from_shares(conn,smb_shares,"")

    users, groups = get_users_and_groups(ip, '', '')
    if users or groups:
        log_success(f"Found smb users: {','.join(users)} groups: {','.join(groups)}")
    else: log_info("No smb users or groups found")

