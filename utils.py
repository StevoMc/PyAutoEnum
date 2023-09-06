import subprocess
import requests
import re
from urllib.parse import urlparse
from tabulate import tabulate
from collections import OrderedDict
import socket
import time

logs=[]

def get_hostnames(ip, port):
    hostnames = []
    for protocol in ["https", "http"]:
        hostname = get_hostname_from_header(ip, port, protocol)
        if hostname and [hostname, protocol] not in hostnames:
            if process_new_hostname(hostname):
                try:
                    if socket.gethostbyname(hostname) == ip:
                        hostnames.append([hostname, protocol])
                except socket.gaierror:
                    pass
        try:
            response = requests.get(f"{protocol}://{ip}:{port}", timeout=2)
            if response.status_code == 200 and [ip, protocol] not in hostnames:
                hostnames.append([ip, protocol])
        except requests.RequestException as e:
            if protocol == "http" and "host=" in str(e) and "Failed to resolve" in str(e):
                unresolved_host = re.search(r"Failed to resolve '(.+?)'", str(e)).group(1)
                if process_new_hostname(unresolved_host) and [unresolved_host, protocol] not in hostnames:
                    try:
                        if socket.gethostbyname(hostname) == ip:
                            hostnames.append([unresolved_host,protocol])
                    except socket.gaierror:
                        pass
    return hostnames


def get_hostname_from_header(ip, port, protocol):
    try:
        url = f"{protocol}://{ip}:{port}"
        response = requests.head(url, timeout=1)
        if 'location' in response.headers:
            location = response.headers['location']
            parsed_url = urlparse(location)
            return parsed_url.hostname
    except:
        pass
    return None


def check_target_up(ip):
    try:
        output = subprocess.check_output(f"ping -c 2 {ip}", shell=True, timeout=5)
        return True
    except subprocess.CalledProcessError:
        return False
    except subprocess.TimeoutExpired:
        return False


def merge_dicts(dict1, dict2):
    result = dict1.copy()

    for key, value in dict2.items():
        if key in dict1:
            if isinstance(dict1[key], dict) and isinstance(value, dict):
                result[key] = merge_dicts(dict1[key], value)
            elif isinstance(dict1[key], list) and isinstance(value, list):
                # Append non-duplicate items
                result[key] = dict1[key] + [item for item in value if item not in dict1[key]]
            else:
                if dict1[key] and value and dict1[key] != value:
                    result[key] = str(dict1[key]) + ", " + str(value)
                elif not dict1[key] and value:
                    result[key] = value
                elif dict1[key] and not value:
                    result[key] = dict1[key]
        else:
            result[key] = value

    return result


def write_log(text):
    logs.append(str(text))
    with open("logs.txt", "a") as file:
        file.write(str(text)+"\n")
        file.close()

def get_logs():
    return logs


def check_resolve_host(hostname):
    try:
        socket.gethostbyname(hostname)
        return True
    except socket.gaierror:
        return False


def check_http_connection(protocol,ip,port,timeout=2):
    try:
        response = requests.get(f"{protocol}://{ip}:{port}", timeout=timeout)
        if response.status_code == 200:
            return True
    except requests.RequestException as e:
        return False

def process_new_hostname(hostname):
    from scan import get_command
    if check_resolve_host(hostname):
        return True
    else:
        write_log(f"[!] Non resolvable hostname found: {hostname}")
        write_log("[*] Add the host to /etc/hosts ('add') or ignore this warning ('ignore')")
        cmd = get_command()
        while cmd != "add" and cmd != "ignore":
            time.sleep(1)
            cmd = get_command()

        if cmd == "add":
            write_log("[+] Checking if host can get resolved now ...")
            if check_resolve_host(hostname):
                write_log(f"[+] Successfully resolved {hostname}")
                return True
            else:
                write_log(f"[!] Could not resolve hostname {hostname}")
                write_log("[!] Exiting ...")
                exit(1)
        if cmd == "ignore":
            write_log(f"[!] Ignoring host resolve warning for {hostname}")
            return False


def truncate_value(value, width):
    if len(value) > width:
        return value[:width-3] + "..."
    return value

def get_console_width():
    try:
        width = int(subprocess.check_output(['tput', 'cols']))
        return width
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
