import threading
import traceback
from core.utils import *
from core.config import Config
from core.attack_thread import AttackThread
from core.data_classes import *
from custom_modules import *

class ScanManager:
    """
    Manages the scanning process for a given target.
    """

    def start_scan(self):
        """
        Start scanning the target, storing results in the TargetInfo instance.
        """
        target = Config.target_info.get_host()
        if not target:
            Config.log_error("No valid target specified")
            
        Config.log_info(f"Starting Enum for {target}:")

        if not check_target_up(target):
            Config.log_warning(f"Target {target} DID NOT respond to PING")
        else:
            Config.log_success("Target is up")

        # If no open ports exist, perform an NMAP scan
        if not Config.target_info.get_ports():
            nmap_ports = "-p 443" # TODO testing       
            nmap_args =   ["-Pn","-sV", nmap_ports, "-T4"]
            Config.log_info(f"Started Fast NMAP Scan (nmap {target} {nmap_args})")
            nmap_results = check_open_ports(Config.target_info, None, nmap_args)
            Config.log_info(nmap_results)
            if nmap_ports:
                Config.target_info.merge(nmap_results)

        # SMB Enumeration if port 445 is open
        if "445" in Config.target_info.get_ports():
            smb_module = next((m for m in Config.modules if m.name.lower() == "smb_enum_anon"), None)
            if smb_module:
                AttackThread(
                    target_info=Config.target_info,
                    module=smb_module,
                    port=445,
                    protocol="smb",
                    hostname=Config.target_info.ip
                ).start()

        # Start attacks that do not require a specific protocol
        self.start_attack_modules()        


    def start_attack_modules(self):
        """
        Start attack modules for a given protocol and target.
        """
        
        for port in Config.target_info.ports:            
            for module in Config.modules:
                port_data = Config.target_info.get_port(port)        
                if port_data:    
                    if module.meets_requirements(port_data):
                        """ start module """
                        AttackThread(
                            target_info=Config.target_info,
                            module=module,
                            port=port
                        ).start()
                        
        for module in Config.modules:
            Config.log_info(f"{module.name} {module.protocol_list}")
            if not module.protocol_list:
                AttackThread(
                    target_info=Config.target_info,
                    module=module,
                    port=None
                ).start()
            


class ScanThread(threading.Thread):
    """
    Manages a scanning process in a separate thread using a ScanManager.
    """

    def __init__(self):
        """
        Initializes the scanning thread.

        :param target_info: Instance of TargetInfo containing all scan-related data.
        """
        super().__init__()
        self.scan_manager = ScanManager()
        self.finished = False
        self.daemon = True

    def run(self):
        """
        Executes the scan in a separate thread and marks it as finished upon completion.
        """
        try:
            self.scan_manager.start_scan()
            self.finished = True
        except Exception:
            Config.log_error(f"Exception in ScanThread: {traceback.format_exc()}")
