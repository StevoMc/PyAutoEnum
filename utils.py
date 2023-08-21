import subprocess
import requests
import re
from urllib.parse import urlparse
from tabulate import tabulate


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


def write_log(text):
    logs.append(str(text))
    with open("logs.txt", "a") as file:
        file.write(str(text)+"\n")
        file.close()

def get_logs():
    return logs
