from smb.SMBConnection import SMBConnection as samr
from core.config import *
import os
import random
import string
#from impacket.dcerpc.v5 import samr, transport


def get_users_and_groups(target_ip, username="", password=""):
    try:
        binding = r'ncacn_np:%s[\pipe\samr]' % target_ip
        rpctransport = transport.DCERPCTransportFactory(binding)
        rpctransport.set_credentials(username, password)

        dce = rpctransport.get_dce_rpc()
        dce.connect()
        dce.bind(samr.MSRPC_UUID_SAMR)

        resp = samr.hSamrConnect(dce)
        server_handle = resp['ServerHandle']

        resp = samr.hSamrEnumerateDomainsInSamServer(dce, server_handle)

        if 'Buffer' not in resp or not resp['Buffer']['Buffer']:
            return [], []

        domain_sid = resp['Buffer']['Buffer'][0]['Sid']

        resp = samr.hSamrLookupDomainInSamServer(dce, server_handle, domain_sid)
        domain_handle = resp['DomainHandle']

        # Get users
        resp = samr.hSamrEnumerateUsersInSamDomain(dce, domain_handle)
        users = [entry['Name'] for entry in resp['Buffer']['Buffer']]

        # Get groups
        resp = samr.hSamrEnumerateGroupsInSamDomain(dce, domain_handle)
        groups = [entry['Name'] for entry in resp['Buffer']['Buffer']]

        dce.disconnect()
        return users, groups

    except Exception as e:
        return [], []

def is_readable(conn, share_name):
    try:
        conn.listPath(share_name, '/')
        return True
    except:
        return False


def is_writeable(conn, share_name):
    test_dir_path = f"/{''.join(random.choices(string.ascii_letters + string.digits, k=20))}.txt"
    try:
        # Versuchen Sie, ein Testverzeichnis zu erstellen
        conn.createDirectory(share_name, test_dir_path)
        # Wenn erfolgreich, löschen Sie das Testverzeichnis
        conn.deleteDirectory(share_name, test_dir_path)
        return True
    except:
        return False


def get_smb_shares(conn):
    # Liste der Shares abrufen
    shares = conn.listShares()

    # Erstellen Sie ein Wörterbuch aus Shares mit Attributen
    share_attributes = {}
    for share in shares:
        share_name = share.name
        share_attributes[share_name] = {
            'readable': is_readable(conn, share_name),
            'writeable': is_writeable(conn, share_name)
        }
    return share_attributes


def download_files_from_shares(conn, shares_dict, working_dir):
    local_directory = working_dir+"smb_files"
    if not os.path.exists(local_directory):
        os.makedirs(local_directory)

    files_downloaded = 0
    for share_name, attributes in shares_dict.items():
        if attributes['readable']:
            try:
                files = conn.listPath(share_name, '/')
                if len(files) < 10:
                    for file in files:
                        if not file.isDirectory:  # Überprüfen, ob es sich um eine Datei und nicht um ein Verzeichnis handelt
                            file_path = os.path.join(local_directory, file.filename)
                            with open(file_path, 'wb') as local_file:
                                conn.retrieveFile(share_name, '/' + file.filename, local_file)
                                files_downloaded+=1
            except:
                Config.log_warning(f"Error downloading smb files from {share_name}")
    if files_downloaded > 0:
        Config.log_success(f"Downloaded a total of {files_downloaded} from smb")
