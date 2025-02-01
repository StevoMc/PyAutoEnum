import yaml
from ping3 import ping
import shutil
from bs4 import BeautifulSoup
import requests
import re
from urllib.parse import urlparse
import socket
import time
import traceback
from core.logging_utils import log_error,log_info,log_success,log_warning

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

def get_hostname_from_url(url):
    parsed_url = urlparse(url)
    return parsed_url.hostname if parsed_url.hostname else url

def check_target_up(ip):
    response = ping(ip, timeout=5)
    return response is not None


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
    if check_resolve_host(hostname):
        return True
    else:
        log_warning(f"Non resolvable hostname found: {hostname}")
        log_warning("Add the host to /etc/hosts ('add') or ignore this warning ('ignore')")
        from core.scan_manager import get_command
        from ui.commands import prompt_lock
        with prompt_lock:
            cmd = get_command()
            while cmd != "add" and cmd != "ignore":
                time.sleep(1)
                cmd = get_command()

            if cmd == "add":
                log_info("Checking if host can get resolved now ...")
                if check_resolve_host(hostname):
                    log_success(f"[+] Successfully resolved {hostname}")
                    return True
                else:
                    log_error(f"Could not resolve hostname {hostname}")
                    log_error("[!] Exiting ...")
                    exit(1)
            if cmd == "ignore":
                log_warning(f"[!] Ignoring host resolve warning for {hostname}")
                return False


def truncate_value(value, width):
    if len(value) > width:
        return value[:width-3] + "..."
    return value


def get_console_width():
    try:
        return shutil.get_terminal_size().columns
    except AttributeError:
        return None  # Fallback if running on an unsupported environment


def is_default_page(response):
    try:
        soup = BeautifulSoup(response.content, 'html.parser')
        headers = response.headers

        if "Apache Server" in soup.text and "Thank you for using Apache" in soup.text:
            return "Apache Default Page"
        elif "Welcome to nginx!" in soup.title.string and "nginx web server" in soup.text:
            if headers.get('Server', '').startswith('nginx'):
                return "Nginx Default Page"
        elif "IIS Windows Server" in soup.text and "Start Internet Information Services (IIS)" in soup.text:
            if headers.get('Server', '').startswith('Microsoft-IIS'):
                return "IIS Default Page"
        elif "If you're seeing this, you've successfully installed Tomcat. Congratulations!" in soup.text and "Apache Tomcat/" in soup.text:
            return "Tomcat Default Page"
        elif "lighttpd powers several popular Web 2.0 sites" in soup.text and "Performance is a key value for Lighttpd" in soup.text:
            if headers.get('Server', '').startswith('lighttpd'):
                return "Lighttpd Default Page"
        elif "This web server is powered by Cherokee" in soup.text and "It works!" in soup.text:
            if headers.get('Server', '').startswith('Cherokee'):
                return "Cherokee Default Page"
        else:
            return None
    except:
        log_error(traceback.format_exc())
        
        
def load_modules(config_file):
    # Load file
    with open(config_file, "r", encoding="utf-8") as file:
        modules = yaml.safe_load(file)
        
    checked_modules = []
    failed_modules = []    
    for attack in modules:
        if check_command_installed(attack.get("command")): 
            checked_modules.append(attack)    
        else: 
            failed_modules.append(attack.get("name"))            
            
    count_loaded = len(modules)
    count_errors = len(failed_modules)
    log_success(f"Loaded {count_loaded-count_errors}/{count_loaded} Attack Modules")
    if failed_modules: 
        log_warning(f"Failed to load {len(failed_modules)} Attack Modules: [{','.join(failed_modules)}]")
    
    return checked_modules

def check_command_installed(command):
    """Check if the given command is installed on the system."""
    if shutil.which(command) is None:        
        return False
    return True