#!/usr/bin/env python3
"""
Example usage of PyAutoEnum.
"""

import os
import sys

from pyautoenum.config.manager import ConfigManager
from pyautoenum.data.models import TargetInfo
from pyautoenum.utils.network import check_target_up, is_ip_address


def main():
    """Run a simple demonstration."""
    # Create a ConfigManager instance
    config = ConfigManager()
    config.init_config(path=os.path.join(os.getcwd(), "output"))
    
    # Create a target
    target_ip = "127.0.0.1"  # Use a safe example
    
    # Check if target is valid IP
    if not is_ip_address(target_ip):
        print(f"Error: {target_ip} is not a valid IP address")
        return 1
        
    # Create target info
    target_info = TargetInfo(config, ip=target_ip)
    config.set_target_info(target_info)
    
    # Test if target is up
    if check_target_up(target_ip):
        print(f"Target {target_ip} is up!")
    else:
        print(f"Target {target_ip} did not respond to ping")
    
    # Log some information
    ConfigManager.log_info("Example information message")
    ConfigManager.log_success("Example success message")
    
    # Get recent logs
    recent_logs = ConfigManager.get_logs()[-5:]
    print("\nRecent logs:")
    for log in recent_logs:
        print(f"  {log}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
