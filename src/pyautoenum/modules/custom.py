"""Custom modules for PyAutoEnum."""

import re
import socket
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

import requests
import urllib3
from bs4 import BeautifulSoup
from ping3 import ping

from pyautoenum.config.manager import ConfigManager
from pyautoenum.utils.network import (
    check_http_connection,
    get_hostname_from_url,
    is_default_page,
    is_ip_address,
)

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def subdomain_enum_brute(target_info, port, switches):
    """
    Perform subdomain enumeration using brute force.
    
    Args:
        target_info: Target information object
        port: Port to scan
        switches: Additional parameters
        
    Returns:
        Output of the scan
    """
    hostname = target_info.get_host()
    port_data = target_info.get_port(port)
    protocol = port_data.protocol if port_data else "http"
    
    if not switches or len(switches) == 0:
        raise ValueError("No wordlist provided for subdomain enumeration")
        
    wordlist_path = switches[0]
    discovered_domains = []
    
    try:
        with open(wordlist_path, "r") as wordlist_file:
            for line in wordlist_file:
                subdomain = line.strip()
                if not subdomain or subdomain.startswith("#"):
                    continue
                    
                domain_to_check = f"{subdomain}.{hostname}"
                try:
                    # Try to resolve the domain
                    ip_address = socket.gethostbyname(domain_to_check)
                    discovered_domains.append((domain_to_check, ip_address))
                    
                    # Check if the domain responds on the specified port
                    if check_http_connection(protocol, domain_to_check, port):
                        target_info.add_hostname(port, domain_to_check, protocol)
                        ConfigManager.log_success(f"Found active subdomain: {domain_to_check} ({ip_address})")
                except socket.gaierror:
                    # Domain doesn't resolve
                    pass
    except Exception as e:
        ConfigManager.log_error(f"Error in subdomain enumeration: {str(e)}")
        
    return discovered_domains


def analyse_subdomain_enum_brute(target_info, output):
    """
    Process the results of subdomain enumeration.
    
    Args:
        target_info: Target information object
        output: Output from the subdomain_enum_brute function
    """
    if not output:
        return
        
    subdomains = {domain: ip for domain, ip in output}
    target_info.add_information("subdomains", "enumeration", subdomains)
    
    ConfigManager.log_info(f"Discovered {len(subdomains)} subdomains through brute forcing")


def check_for_http(target_info, port, switches):
    """
    Check if a port is running an HTTP server.
    
    Args:
        target_info: Target information object
        port: Port to check
        switches: Additional parameters
        
    Returns:
        Boolean indicating if HTTP service was detected
    """
    hostname = target_info.get_host()
    
    # Try HTTP
    http_available = check_http_connection("http", hostname, port)
    if http_available:
        target_info.get_port(port).protocol = "http"
        ConfigManager.log_success(f"HTTP service detected on port {port}")
        
    # Try HTTPS
    https_available = check_http_connection("https", hostname, port)
    if https_available:
        target_info.get_port(port).protocol = "https"
        ConfigManager.log_success(f"HTTPS service detected on port {port}")
    
    return http_available or https_available


def check_open_ports(target_info, port, switches):
    """
    Scan for open ports using nmap.
    
    Args:
        target_info: Target information object
        port: Port to scan (or None for all ports)
        switches: Additional parameters for nmap
        
    Returns:
        Dictionary with discovered ports
    """
    try:
        import nmap
        
        scanner = nmap.PortScanner()
        target = target_info.get_host()
        
        # Build command
        switches_str = " ".join(switches)
        ConfigManager.log_info(f"Running nmap scan: {target} {switches_str}")
        
        # Run scan
        scanner.scan(target, arguments=switches_str)
        
        # Process results
        discovered_ports = {}
        
        for host in scanner.all_hosts():
            for proto in scanner[host].all_protocols():
                for port_num in scanner[host][proto]:
                    port_info = scanner[host][proto][port_num]
                    
                    port_data = {
                        "protocol": port_info.get("name", ""),
                        "product": port_info.get("product", ""),
                        "version": port_info.get("version", ""),
                        "modules": [],
                        "hostnames": [],
                        "infos": {}
                    }
                    
                    discovered_ports[str(port_num)] = port_data
                    ConfigManager.log_success(f"Discovered port {port_num}/{proto}: {port_data['protocol']} {port_data['product']} {port_data['version']}")
        
        return discovered_ports
    
    except ImportError:
        ConfigManager.log_error("python-nmap not installed. Cannot run port scan.")
        return {}
    except Exception as e:
        ConfigManager.log_error(f"Error in port scan: {str(e)}")
        return {}


def analyse_full_nmap(target_info, output):
    """
    Process the full nmap scan results.
    
    Args:
        target_info: Target information object
        output: Output from nmap scan
    """
    pass  # Handled directly by check_open_ports function


def create_wordlist_from_website(target_info, port, switches):
    """
    Create a custom wordlist by scraping website content.
    
    Args:
        target_info: Target information object
        port: Target port
        switches: Additional parameters
        
    Returns:
        List of extracted words
    """
    hostname = target_info.get_host()
    port_data = target_info.get_port(port)
    if not port_data or not port_data.protocol:
        ConfigManager.log_error(f"No protocol information available for port {port}")
        return []
        
    url = f"{port_data.protocol}://{hostname}:{port}"
    
    try:
        response = requests.get(url, verify=False, timeout=10)
        if not response.ok:
            ConfigManager.log_error(f"Failed to fetch content from {url}: {response.status_code}")
            return []
            
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Extract text
        text_content = soup.get_text()
        
        # Extract words
        words = re.findall(r'\b[a-zA-Z0-9_-]{3,15}\b', text_content)
        unique_words = sorted(set(words))
        
        # Save wordlist
        wordlist_path = f"{ConfigManager.path}/wordlist_{hostname}_{port}.txt"
        with open(wordlist_path, "w") as f:
            for word in unique_words:
                f.write(f"{word}\n")
                
        ConfigManager.log_success(f"Created wordlist with {len(unique_words)} unique words at {wordlist_path}")
        return unique_words
        
    except Exception as e:
        ConfigManager.log_error(f"Error creating wordlist: {str(e)}")
        return []
