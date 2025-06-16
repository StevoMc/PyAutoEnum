"""Main entry point for PyAutoEnum."""

import argparse
import signal
import sys

from pyautoenum.config.manager import ConfigManager
from pyautoenum.core.scan import ScanManager
from pyautoenum.data.models import TargetInfo
from pyautoenum.ui.interface import Interface
from pyautoenum.utils.network import get_hostname_from_url, is_ip_address


def exit_handler(sig, frame):
    """Handle exit signals gracefully."""
    ConfigManager.log_warning("\nCtrl+C detected!")
    if ConfigManager.target_info:
        ConfigManager.target_info.save_to_file()
    sys.exit(0)


def main(window=None):
    """Main entry point for the application.
    
    Args:
        window: Curses window object when called via curses.wrapper, can be None when called directly
    """
    # Set up signal handler for graceful exit
    signal.signal(signal.SIGINT, exit_handler)
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="PyAutoEnum - Automated Enumeration Tool")
    parser.add_argument("--path", help="Path to store output files")
    parser.add_argument("-t", "--target", help="Target IP or hostname", required=True)
    parser.add_argument("--banner", help="Show welcome banner", action="store_true")
    parser.add_argument(
        "-n",
        "--newsession",
        action="store_true",
        help="New session, do not use saved session data",
    )
    args = parser.parse_args()

    # Process target information
    target = args.target
    ip = target if is_ip_address(target) else ""
    hostname_from_url = get_hostname_from_url(target)
    hostname = hostname_from_url if hostname_from_url else "" 
    
    # Initialize configuration
    config_manager = ConfigManager()
    config_manager.init_config(path=args.path)
    config_manager.load_modules()
    
    # Initialize target information
    target_info = TargetInfo(config_manager, ip=ip, hostname=hostname)
    config_manager.set_target_info(target_info)
    
    # Start UI and scanning
    try:
        if args.banner:
            from pyautoenum.ui.banner import show_banner
            show_banner()
        
        interface = Interface()
        interface.start()
        
        scan_manager = ScanManager()
        scan_manager.start_scan()
        
        interface.join()
    except KeyboardInterrupt:
        exit_handler(None, None)
    except Exception as e:
        ConfigManager.log_error(f"Error in main: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
