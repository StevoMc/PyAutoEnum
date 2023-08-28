import subprocess
import requests
import re
from urllib.parse import urlparse
from tabulate import tabulate
from collections import OrderedDict
import socket
import time

logs=[]

def check_protocol(ip, port):
    # Get the hostname for HTTPS first since it's more secure
    hostname = get_hostname(ip, port, "https")
    if hostname == ip:  # If HTTPS hostname is same as IP, try HTTP
        hostname = get_hostname(ip, port, "http")

    for protocol in ["https", "http"]:
        if try_protocol(hostname, port, protocol):
            return protocol
    return ""


def try_protocol(hostname, port, protocol):
    try:
        response = requests.get(f"{protocol}://{hostname}:{port}", timeout=1)
        if response.status_code in [200, 301, 302]:
            return True
    except requests.RequestException as e:
        if protocol == "http":
            handle_http_exception(e)
    return False


def handle_http_exception(exception):
    error_msg = str(exception)
    if "host=" not in error_msg:
        return

    pattern = r"Failed to resolve '(.+?)'"
    match = re.search(pattern, error_msg)

    if match:
        unresolved_host = match.group(1)
        process_new_hostname(hostname)
        write_log(f"Found host {unresolved_host} which is not in /etc/hosts")
        exit()


def get_hostname(ip, port, protocol):
    try:
        url = f"{protocol}://{ip}:{port}"
        response = requests.head(url, timeout=1)
        if 'location' in response.headers:
            location = response.headers['location']
            parsed_url = urlparse(location)
            return parsed_url.hostname or ip
    except requests.RequestException:
        pass
    return ip

def check_target_up(ip):
    try:
        output = subprocess.check_output(f"ping -c 2 {ip}", shell=True, timeout=5)
        return True
    except subprocess.CalledProcessError:
        return False
    except subprocess.TimeoutExpired:
        return False


def filter_dict_by_values(data, key, values):
    filtered_dict = {k: v for k, v in data.items() if v.get(key) in values}
    return filtered_dict


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


def process_new_hostname(hostname):
    from scan import get_command
    if not check_resolve_host(hostname):
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
            else:
                write_log(f"[!] Could not resolve hostname {hostname}")
                write_log("[!] Exiting ...")
                exit(1)
        if cmd == "ignore":
            write_log("[!] Ignoring host resolve warning for ")


