from ping3 import ping
import shutil
from bs4 import BeautifulSoup
import requests
import re
from urllib.parse import urlparse


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
    return parsed_url.hostname if parsed_url.hostname else None

def check_target_up(ip):
    response = ping(ip, timeout=5)
    return response is not None

def is_ip_address(string):
    """Checks if the string is a valid IPv4 or IPv6 address."""
    # Regular expression for validating IPv4 address
    ipv4_pattern = re.compile(r'^(\d{1,3}\.){3}\d{1,3}$')
    if ipv4_pattern.match(string):
        # Check if all octets are between 0 and 255
        parts = string.split('.')
        if all(0 <= int(part) <= 255 for part in parts):
            return True
    
    # Regular expression for validating IPv6 address
    ipv6_pattern = re.compile(r'^[0-9a-fA-F:]{2,39}$')
    if ipv6_pattern.match(string):
        return True
    
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


def check_http_connection(protocol,ip,port,timeout=2):
    try:
        response = requests.get(f"{protocol}://{ip}:{port}", timeout=timeout)
        if response.status_code == 200:
            return True
    except requests.RequestException as e:
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
        return None