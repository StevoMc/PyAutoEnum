import threading
import subprocess
import os
from attackThread import AttackThread


def nikto(protocol,hostname, port):
    nikto = AttackThread(f"nikto_{port}", port, ["/usr/bin/nikto", "--url", f"{protocol}://{hostname}:{port}"])
    nikto.start()
    return nikto

def wfuzz_sub_brute(protocol,hostname,port):
    fuzz_hide_cmd = f'echo "www" | wfuzz -c -z stdin -H "Host:FUZZ.{hostname}" -u {protocol}://{hostname}:{port} 2>/dev/null | grep -oP "\b[0-9]+(?=\sCh\b)"'
    fuzz_hide_value=str(os.system(fuzz_hide_cmd))
    sub_brute = AttackThread(f"WFUZZ_Sub_Brute_{port}", port, ["/usr/bin/wfuzz", "-u", f"{protocol}://{hostname}:{port}","-c","-w","/usr/share/seclists/Discovery/DNS/subdomains-top1million-20000.txt","-H",f"Host:FUZZ.{hostname}","--hh",fuzz_hide_value])
    sub_brute.start()
    return sub_brute

def feroxbuster(protocol,hostname,port):
    feroxbuster = AttackThread(
        f"feroxbuster_{port}", port, ["/usr/bin/feroxbuster",
                        "-u",
                        f"{protocol}://{hostname}:{port}/",
                        "-A",
                        "-E",
                        "--no-state",
                        "--smart",
                        "--threads",
                        "150",
                        "-C",
                        "404",
                        "-w", "/usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt"])
    feroxbuster.start()
    return feroxbuster


def cmsScan(protocol,hostname,port):
    cmsScan = AttackThread(f"cmsScan_{port}", port, ["/usr/bin/python", "/home/kali/tools/CMSeeK/cmseek.py", "-u", f"{protocol}://{hostname}:{port}", "--batch", "-r"])
    cmsScan.start()
    return cmsScan
