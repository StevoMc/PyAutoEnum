"""Main entry point for PyAutoEnum."""

import argparse
import signal
import sys
import time
import traceback

from pyautoenum.config.manager import ConfigManager
from pyautoenum.core.attack_thread import attack_thread_pool
from pyautoenum.core.scan import ScanThread
from pyautoenum.data.models import TargetInfo
from pyautoenum.ui.interface import Interface
from pyautoenum.ui.simple_interface import SimpleInterface
from pyautoenum.utils.network import get_hostname_from_url, is_ip_address


def exit_handler(sig, frame):
    """Handle exit signals gracefully."""
    ConfigManager.log_warning("\nCtrl+C detected!")
    
    # Restore cursor visibility
    try:
        import curses
        curses.endwin()
        curses.curs_set(1)  # Ensure cursor is visible
    except Exception:
        pass  # Ignore if curses not initialized
    
    # Stop the scan thread if it's running
    if ConfigManager.scan_thread:
        ConfigManager.scan_thread.stop()
        
    # Stop the thread pool
    attack_thread_pool.stop()
    
    # Save target info before exiting
    if ConfigManager.target_info:
        ConfigManager.target_info.save_to_file()
    
    # Allow a short moment for cleanup before forcing exit
    time.sleep(0.5)
        
    # Force exit to make sure all threads terminate
    sys.exit(0)


def main():
    """Main entry point for the application."""
    # Set up signal handler for graceful exit
    signal.signal(signal.SIGINT, exit_handler)
    
    # Check terminal setup for curses compatibility
    import os
    if os.environ.get("TERM") is None:
        os.environ["TERM"] = "xterm-256color"
        print("Warning: TERM environment variable not set, defaulting to xterm-256color")
    
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
    parser.add_argument(
        "--no-ui",
        action="store_true",
        help="Run without the interactive UI",
    )
    parser.add_argument(
        "--debug-ui",
        action="store_true",
        help="Enable debug output for UI issues",
    )
    parser.add_argument(
        "--ui-type",
        choices=["auto", "simple", "full"],
        default="auto",
        help="Select UI type: auto (default), simple, or full",
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
    interface = None
    scan_thread = None
    try:
        if args.banner:
            from pyautoenum.ui.banner import show_banner
            show_banner()
        
        # Check terminal environment if UI is enabled
        if not args.no_ui:
            import os
            term = os.environ.get("TERM")
            if not term:
                print("Warning: No TERM environment variable set. UI may not display correctly.")
                print("Consider using the --no-ui flag if you experience issues.")
            
            # Debug mode setup
            if args.debug_ui:
                print("Debug UI mode enabled")
                print(f"Terminal type: {term}")
                print(f"Terminal dimensions: {os.get_terminal_size().columns}x{os.get_terminal_size().lines}")
                print(f"Python: {sys.version}")
                if os.isatty(sys.stdout.fileno()):
                    print("Running in an interactive terminal")
                else:
                    print("Not running in an interactive terminal")
                
                # Check for common terminal environment variables
                env_vars = ["TERM", "COLORTERM", "TERMINFO", "LINES", "COLUMNS"]
                for var in env_vars:
                    print(f"{var}={os.environ.get(var, 'Not set')}")
                    
            # Reset terminal before starting UI
            os.system('reset')  # This ensures terminal is in a clean state
                    
            # Select appropriate interface based on command line args
            if args.ui_type == "simple":
                # Use simple interface
                print("Using simplified interface")
                interface = SimpleInterface()
            elif args.ui_type == "full":
                # Use full interface
                print("Using full feature interface")
                interface = Interface()
            else:  # auto mode
                # Try to determine the best interface
                try:
                    # Check if we're in a compatible terminal
                    import subprocess
                    term_info = subprocess.run(["tput", "longname"], 
                                            stdout=subprocess.PIPE, 
                                            stderr=subprocess.PIPE)
                    term_name = term_info.stdout.decode('utf-8').strip()
                    
                    if "256" in term_name or "color" in term_name.lower():
                        print(f"Detected compatible terminal: {term_name}")
                        print("Using full featured interface")
                        interface = Interface()
                    else:
                        print(f"Detected basic terminal: {term_name}")
                        print("Using simplified interface")
                        interface = SimpleInterface()
                except Exception:
                    # Default to simple interface on any error
                    print("Could not detect terminal type, using simplified interface")
                    interface = SimpleInterface()
                    
            # Initialize the selected interface
            ConfigManager.set_ui_interface(interface)
            interface.start()
                
            # Allow UI to initialize
            time.sleep(1.0)  # Give more time for UI initialization
        else:
            print(f"Running in non-interactive mode. Scanning target: {target}")
        
        # Start scanning thread
        scan_thread = ScanThread()
        ConfigManager.set_scan_thread(scan_thread)
        
        # Set initial UI status
        if ConfigManager.ui_interface:
            ConfigManager.ui_interface.set_status(f"Starting scan of {target}")
        
        scan_thread.start()
        
        # Instead of waiting for threads to complete, wait for a keyboard interrupt
        try:
            while True:
                time.sleep(0.5)  # Sleep to prevent CPU hogging
        except KeyboardInterrupt:
            pass
            
    except KeyboardInterrupt:
        exit_handler(None, None)
    except Exception as e:
        traceback.print_exc()
        ConfigManager.log_error(f"Error in main: {str(e)}")
        return 1
    finally:
        # Clean up threads before exiting
        if scan_thread and scan_thread.is_alive():
            scan_thread.stop()
        
        # Wait a moment for threads to clean up
        time.sleep(0.5)
        
        # Save any data
        if ConfigManager.target_info:
            ConfigManager.target_info.save_to_file()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
