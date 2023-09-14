from utils import *

def analyse_smb_enum_anon(output):
    pass

def analyse_full_nmap(output):
    from scan import open_ports_lock, open_ports, override_open_ports
    with open_ports_lock:
        override_open_ports(merge_dicts(open_ports,output))
