import subprocess
import requests
from urllib.parse import urlparse
from tabulate import tabulate


def check_protocol(ip, port):
    hostname_for_http =  get_hostname(ip,port,"http")
    hostname_for_https = get_hostname(ip,port,"https")

    if hostname_for_http != ip:
        ip = hostname_for_http
    elif hostname_for_https != ip:
        ip = hostname_for_https

    try:
        response = requests.get(f"https://{ip}:{port}", timeout=5)
        if response.status_code in [200,301]:
            return 'https'
    except (requests.RequestException, ConnectionError) as e:
        pass

    try:
        response = requests.get(f"http://{ip}:{port}", timeout=5)
        if response.status_code in [200,301]:
            return 'http'
    except (requests.RequestException) as e:
        error_msg = str(e)
        if "host=" not in error_msg:
            return None
        start_index = error_msg.find("Failed to resolve '") + len("Failed to resolve '")
        end_index = error_msg.find("'", start_index)
        if start_index >= 0 and end_index >= 0:
            unresolved_host = error_msg[start_index:end_index]
            print(f"Found host {unresolved_host} which is not in /etc/hosts")
            print("Exiting...")
            exit()

    return None


def get_hostname(ip, port,protocol):
    try:
        url = f"{protocol}://{ip}:{port}"
        response = requests.head(url)
        if 'location' in response.headers:
            location = response.headers['location']
            parsed_url = urlparse(location)
            if parsed_url.hostname:
                return parsed_url.hostname
        return ip
    except requests.RequestException:
        return ip


def check_target_up(ip):
    try:
        output = subprocess.check_output(f"ping -c 2 {ip}", shell=True, timeout=5)
        return True
    except subprocess.CalledProcessError:
        return False
    except subprocess.TimeoutExpired:
        return False


def print_data(data):
    print("")
    headers = None
    rows = []

    for key, value in data.items():
        if isinstance(value, dict):
            if headers is None:
                headers = ["Port"] + list(value.keys())
            row = [key] + list(value.values())
            rows.append(row)

    if headers is not None:
        table = tabulate(rows, headers=headers, tablefmt="pipe")
        print(table)
    else:
        print("No data to display.")

    print("")

def filter_dict_by_values(data, key, values):
    filtered_dict = {k: v for k, v in data.items() if v.get(key) in values}
    return filtered_dict
