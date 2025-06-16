"""Network utility functions for PyAutoEnum."""

import re
import shutil
import socket
from urllib.parse import urlparse

import requests
import urllib3
from bs4 import BeautifulSoup
from ping3 import ping


def get_hostname_from_header(ip, port, protocol="http"):
    """
    Extract hostname from HTTP headers.
    
    Args:
        ip: IP address to connect to
        port: Port number
        protocol: Protocol to use (http/https)
        
    Returns:
        Hostname from Location header or None
    """
    try:
        url = f"{protocol}://{ip}:{port}"
        response = requests.head(url, timeout=1, verify=False)
        if "location" in response.headers:
            location = response.headers["location"]
            parsed_url = urlparse(location)
            return parsed_url.hostname
    except:
        pass
    return None


def get_hostname_from_url(url):
    """
    Extract hostname from a URL.
    
    Args:
        url: URL to parse
        
    Returns:
        Hostname from URL or None
    """
    parsed_url = urlparse(url)
    return parsed_url.hostname if parsed_url.hostname else None


def check_target_up(ip):
    """
    Check if a target responds to ping.
    
    Args:
        ip: IP address to check
        
    Returns:
        Boolean indicating if target responded
    """
    response = ping(ip, timeout=5)
    return response is not None


def is_ip_address(string):
    """
    Check if a string is a valid IPv4 or IPv6 address.
    
    Args:
        string: String to check
        
    Returns:
        Boolean indicating if string is an IP address
    """
    # Regular expression for validating IPv4 address
    ipv4_pattern = re.compile(r"^(\d{1,3}\.){3}\d{1,3}$")
    if ipv4_pattern.match(string):
        # Check if all octets are between 0 and 255
        parts = string.split(".")
        if all(0 <= int(part) <= 255 for part in parts):
            return True

    # Regular expression for validating IPv6 address
    ipv6_pattern = re.compile(r"^[0-9a-fA-F:]{2,39}$")
    if ipv6_pattern.match(string):
        return True

    return False


def check_http_connection(protocol, ip, port, timeout=5):
    """
    Check if an HTTP connection can be established.
    
    Args:
        protocol: Protocol to use (http/https)
        ip: IP address or hostname
        port: Port number
        timeout: Connection timeout in seconds
        
    Returns:
        Boolean indicating if connection succeeded
    """
    try:
        url = f"{protocol}://{ip}:{port}"
        response = requests.get(url, timeout=timeout, verify=False)
        # Consider any 2xx status code as a successful response
        return response.ok
    except (requests.ConnectionError, requests.Timeout, requests.RequestException):
        pass
    return False


def truncate_value(value, width):
    """
    Truncate a string to fit within a given width.
    
    Args:
        value: String to truncate
        width: Maximum width
        
    Returns:
        Truncated string with ellipsis if needed
    """
    value_str = str(value)
    if len(value_str) > width:
        return value_str[:width-3] + "..."
    return value_str


def get_console_width():
    """
    Get the width of the console.
    
    Returns:
        Console width or None if not available
    """
    try:
        return shutil.get_terminal_size().columns
    except AttributeError:
        return 80  # Default fallback width


def is_default_page(response):
    """
    Check if a response contains a default web page.
    
    Args:
        response: HTTP response object
        
    Returns:
        Boolean indicating if it's likely a default page
    """
    try:
        soup = BeautifulSoup(response.content, "html.parser")
        headers = response.headers
        
        # Common keywords in default pages
        default_page_keywords = [
            "default", "welcome", "test page", "it works", 
            "apache", "nginx", "iis", "index", "default page"
        ]
        
        # Check page title
        title = soup.title.text.lower() if soup.title else ""
        if any(keyword in title for keyword in default_page_keywords):
            return True
            
        # Check common server headers
        server = headers.get("Server", "").lower()
        if server and not any(cms in server.lower() for cms in ["wordpress", "drupal", "joomla"]):
            body_text = soup.get_text().lower()
            if any(keyword in body_text for keyword in default_page_keywords):
                return True
                
        # Check for minimal content
        content_length = int(headers.get("Content-Length", "0"))
        if content_length < 1000:  # Small pages are often default pages
            body_text = soup.get_text().lower()
            word_count = len(body_text.split())
            if word_count < 50:  # Few words often indicates a default page
                return True
                
        return False
    except:
        return False
