# FEDORA IS BROKEN FOR NOW

from . import fetch_url, extract_links
import re
from bs4 import BeautifulSoup


def fetch_fedora_versions(config):
    versions_list = []
    base_url = config.get("base_url")
    if not base_url:
        error_msg = "fetch_fedora_versions: 'base_url' not found in config"
        print(error_msg)
        return []
    
    try:
        result = fetch_url(base_url, timeout=10, error_prefix="Error fetching Fedora versions")
        print(f"Debug: fetch_url returned type: {type(result)}")
        print(f"Debug: fetch_url returned length: {len(result) if hasattr(result, '__len__') else 'No length'}")
        print(f"Debug: fetch_url returned: {result}")
        
        if not result:
            print(f"fetch_fedora_versions: No result from fetch_url for {base_url}")
            return []
            
        if isinstance(result, tuple) and len(result) == 2:
            soup, error = result
        else:
            print(f"fetch_fedora_versions: Unexpected result format from fetch_url: {result}")
            return []
            
        if error:
            print(f"fetch_fedora_versions: {error}")
            return []
            
        if not soup:
            print(f"fetch_fedora_versions: Empty content returned from {base_url}")
            return []
            
        if isinstance(soup, str):
            soup = BeautifulSoup(soup, 'html.parser')
    except ValueError as e:
        print(f"fetch_fedora_versions: Unpacking error: {e}")
        print(f"fetch_fedora_versions: Result was: {result}")
        return []
    except Exception as e:
        print(f"fetch_fedora_versions: Unexpected error: {e}")
        print(f"fetch_fedora_versions: Result was: {result}")
        return []
    
    links = extract_links(soup, base_url)
    
    version_items = {}
    for link_text, url in links.items():
        if re.match(r"^[0-9]+/?$", link_text):
            version_num = link_text.strip("/")
            version_items[version_num] = url
    
    versions_list = sorted(version_items.keys(), key=int, reverse=True)
    
    result = []
    for version in versions_list:
        result.append({
            "name": version,
            "id": version,
            "url": version_items[version]
        })
    
    return result


def fetch_fedora_isos(version_url):
    isos = []
    version = version_url.rstrip('/').split('/')[-1]
    
    paths_to_try = [
        f"{version_url}/Workstation/x86_64/iso/",
        f"{version_url}/Spins/x86_64/iso/", 
        f"{version_url}/Server/x86_64/iso/",
    ]
    
    for path in paths_to_try:
        try:
            result = fetch_url(path, timeout=15, error_prefix=f"Error fetching Fedora ISOs")
            if not result:
                print(f"fetch_fedora_isos: No result from fetch_url for {path}")
                continue
                
            if isinstance(result, tuple) and len(result) == 2:
                soup, error = result
            else:
                print(f"fetch_fedora_isos: Unexpected result format from fetch_url: {result}")
                continue
                
            if error:
                print(f"fetch_fedora_isos: {error}")
                continue
                
            if not soup:
                print(f"fetch_fedora_isos: Empty content returned from {path}")
                continue
                
            if isinstance(soup, str):
                soup = BeautifulSoup(soup, 'html.parser')
                
            iso_links_dict = extract_links(soup, path)
            
            iso_links = {name: url for name, url in iso_links_dict.items() 
                        if name.endswith('.iso') or url.endswith('.iso')}
            
            for iso_name, iso_url in iso_links.items():
                if not iso_url.endswith(".iso"):
                    continue
                    
                iso_filename = iso_url.split('/')[-1]
                display_name = _get_fedora_iso_display_name(iso_filename, version)
                
                isos.append({
                    "name": display_name,
                    "url": iso_url
                })
        except Exception as e:
            print(f"fetch_fedora_isos: Error processing {path}: {e}")
            continue
    
    return isos


def _get_fedora_iso_display_name(filename, version):
    arch_match = re.search(r'(x86_64|i386|aarch64|ppc64le|s390x)', filename)
    arch = arch_match.group(1) if arch_match else "unknown"
    
    if "Workstation" in filename:
        return f"Workstation ({arch})"
    elif "Server" in filename:
        return f"Server ({arch})"
    elif "Silverblue" in filename:
        return f"Silverblue ({arch})"
    elif "Kinoite" in filename:
        return f"Kinoite ({arch})"
    elif "IoT" in filename:
        return f"IoT ({arch})"
    elif "KDE" in filename:
        return f"KDE Spin ({arch})"
    elif "Xfce" in filename:
        return f"Xfce Spin ({arch})"
    elif "MATE" in filename:
        return f"MATE-Compiz Spin ({arch})"
    elif "Cinnamon" in filename:
        return f"Cinnamon Spin ({arch})"
    elif "LXDE" in filename or "LXQt" in filename:
        return f"LXQt Spin ({arch})"
    elif "i3" in filename:
        return f"i3 Spin ({arch})"
    elif "Sway" in filename:
        return f"Sway Spin ({arch})"
    elif "Budgie" in filename:
        return f"Budgie Spin ({arch})"
    elif "Games" in filename:
        return f"Games Lab ({arch})"
    elif "Design" in filename:
        return f"Design Suite Lab ({arch})"
    elif "Python" in filename:
        return f"Python Classroom Lab ({arch})"
    elif "Security" in filename:
        return f"Security Lab ({arch})"
    elif "Astronomy" in filename:
        return f"Astronomy Lab ({arch})"
    elif "Robotics" in filename:
        return f"Robotics Suite Lab ({arch})"
    elif "Jam" in filename:
        return f"Jam Lab ({arch})"
    elif "Everything" in filename:
        return f"Everything ({arch})"
    elif "Live" in filename:
        return f"Live ({arch})"
    elif "dvd" in filename.lower() or "DVD" in filename:
        return f"DVD ({arch})"
    elif "netinst" in filename.lower() or "boot" in filename.lower():
        return f"Network Install ({arch})"
    else:
        name = filename.replace(".iso", "").replace(f"-{version}", "")
        name = name.replace("Fedora-", "").replace("-x86_64", "").replace("-" + arch, "")
        return f"{name} ({arch})"
