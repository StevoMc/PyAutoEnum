from core.utils import *

def analyse_smb_enum_anon(output):
    pass

def analyse_full_nmap(output):
    from core.scan_manager import open_ports_lock, open_ports, override_open_ports
    with open_ports_lock:
        override_open_ports(merge_dicts(open_ports,output))

def analyse_wfuzz_sub_brute(output):
    from core.scan_manager import add_information
    if output:
        port, info = next(iter(output.items()))
        add_information(port,"hostnames",info)
