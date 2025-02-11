from core.smb_utils import *
import nmap
import concurrent.futures
import requests
import time
from core.utils import *
import urllib3
from urllib.parse import urljoin, urlparse

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def custom_modules_tempalte_function(target_info, port, switches):
    pass

def custom_modules_tempalte_analyse(target_info, output): 
    pass


def subdomain_enum_brute(target_info, port, switches):
    protocol = target_info.get_port(port).protocol
    hostname = target_info.get_host() if len(target_info.get_port(port).hostnames) == 0 else target_info.get_port(port).hostnames[0]
    
    if is_ip_address(hostname):
        return {}
    
    url = f"{protocol}://{hostname}:{port}"

    def get_chars_for_subdomain(subdomain,rec_level=0):
        try:
            return len(requests.get(url, headers={"Host":f"{subdomain.strip()}.{hostname}"},timeout=2+rec_level, verify=False, allow_redirects=False).text)
        except:
            if rec_level:
                time.sleep(rec_level)
            if rec_level<=3:
                rec_level+=1
                return get_chars_for_subdomain(subdomain,rec_level)
            else:                
                return 0
        
    if len(switches) > 0:
        wordlist = switches[0]
    else: 
        raise ValueError(f"1 argument needed {len(switches)} given to subdomain_enum_brute")
    
    if os.path.exists(wordlist):
        with open(wordlist) as list:
            subs = list.readlines()
    else: raise FileNotFoundError(f"File {wordlist} not found")
    
    response_www_value = get_chars_for_subdomain("www")
    found_subdomains = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=200) as executor:
        futures = {executor.submit(get_chars_for_subdomain,subdomain.strip()): subdomain for subdomain in subs if subdomain[0] != "#"}
        for future in concurrent.futures.as_completed(futures):
            sub = futures[future]
            if future.result() != response_www_value:
                found_subdomains.append([f"{sub.strip()}.{hostname}",protocol])
    return {str(port):found_subdomains}


def analyse_subdomain_enum_brute(target_info, output):   
    if output: 
        port, info = next(iter(output.items()))
        target_info.add_information(port,"hostnames",info)
        

def check_for_http(target_info, port, switches):
    if check_http_connection("https", target_info.get_host(), port):
        target_info.add_information(port, "protocol", "https")
    elif check_http_connection("http", target_info.get_host(), port):
        target_info.add_information(port, "protocol", "http")
    

# def whatsweb_like_scan(target_info, port, switches):
#     # Crawl Web Data
#     hostname = target_info.get_host()
#     try:
#         protocol = target_info.get_port(port).protocol        
#         url = f"{protocol}://{hostname}:{port}"
#         response = requests.get(url)
#         content = response.text
#         soup = BeautifulSoup(content, 'html.parser')

#         hostname_pattern = re.compile(r'https?://([A-Za-z0-9.-]+)')
#         email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
#         software_version_pattern = re.compile(r'([a-zA-Z\s0-9_-]+)\s*v?\d+\.\d+(\.\d+)?')
#         url_pattern = re.compile(r'https?://[^\s<>"]+|www\.[^\s<>"]+')
#         software_versions = list(set(software_version_pattern.findall(content)))
#         default_page = is_default_page(response)

#         hostnames = list(set(hostname_pattern.findall(content)))
#         hostnames_checked = []
#         for hostname_test in hostnames:
#             try:
#                 if socket.gethostbyname(hostname) == socket.gethostbyname(hostname_test):
#                     if hostname_test not in hostnames_checked:
#                         hostnames_checked.append(hostname_test)
#             except socket.gaierror:
#                 pass

#         crawled_data = {
#             'title':soup.title if soup else "<No Title Found>",
#             'hostnames': hostnames_checked,
#             'emails': list(set(email_pattern.findall(content))),
#             'software_versions': [software[0] for software in software_versions],
#             'urls': list(set(url_pattern.findall(content))),
#             'size': len(response.content),
#             'default_page':default_page,
#             'content':content
#         }
        
#         # Add discovered hostnames
#         for new_hostname in crawled_data["hostnames"]:
#             if check_http_connection("http", new_hostname, port):
#                 target_info.add_hostname(port, new_hostname, "http")
#             if check_http_connection("https", new_hostname, port):
#                 target_info.add_hostname(port, new_hostname, "https")
        
#         target_info.add_information(port, "info", crawled_data)
#     except Exception as e:
#         raise Exception(f"Could not crawl website: {e}")


def check_open_ports(target_info, port, switches):
    nm = nmap.PortScanner()    
    nm.scan(target_info.get_host(), arguments=" ".join(switches))
    
    scan_res = {}
    for host in nm.all_hosts():
        for p in nm[host].get('tcp', {}):
            port_info = {
                'protocol': nm[host]['tcp'][p].get('name', ''),
                'version': nm[host]['tcp'][p].get('version', ''),
                'product': nm[host]['tcp'][p].get('product', ''),
                'hostnames': '',
                'modules': [],
                'info': {}
            }
            scan_res[str(p)] = port_info
        
    return scan_res

def analyse_full_nmap(target_info, output):
    
    target_info.merge(output)


def create_wordlist_from_website(target_info, port, switches):
    try:
        protocol = target_info.get_port(port).protocol
        hostname = target_info.get_host() if len(target_info.get_port(port).hostnames) == 0 else target_info.get_port(port).hostnames[0]
        url = f"{protocol}://{hostname}:{port}"
        
        domain = urlparse(url).netloc
        urls_to_scrape, scraped_urls, all_words = {url}, set(), set()

        while urls_to_scrape:
            current_url = urls_to_scrape.pop()
            if current_url in scraped_urls:
                continue

            try:
                response = requests.get(current_url)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')

                # Extract words
                all_words.update(re.findall(r'\b[a-zA-Z0-9]{5,}\b', soup.get_text()))

                # Extract and filter links
                urls_to_scrape.update(
                    link for link in {urljoin(current_url, a['href']) for a in soup.find_all('a', href=True)}
                    if urlparse(link).netloc == domain and link not in scraped_urls
                )

                scraped_urls.add(current_url)
            except requests.exceptions.RequestException as e:
                pass

        # Generate variants
        variants = set()
        for word in all_words:
            for num in ['', '0', '1', '123', '2024', '2025']:
                for char in ['', '!', '?']:
                    variants.update({word + num + char, word + char})
        
        return '\n'.join(sorted(variants, key=len))

    except Exception as e:
        pass

# def enum_smb(ip, username="", password=""):
#     conn = SMBConnection(username, password, "", str(ip))
#     assert conn.connect(str(ip), 445)

#     smb_shares = get_smb_shares(conn)

#     for share_name,smb_share in smb_shares.items():
#         if smb_share['readable'] or smb_share['writeable']:
#             Config.log_info(f"Found smb share {share_name} read:{smb_share['readable']} write:{smb_share['writeable']}")

#     download_files_from_shares(conn,smb_shares,"")

#     users, groups = get_users_and_groups(ip, '', '')
#     if users or groups:
#         Config.log_success(f"Found smb users: {','.join(users)} groups: {','.join(groups)}")
#     else: Config.log_info("No smb users or groups found")

def analyse_smb_enum_anon(target_info, output):
    pass