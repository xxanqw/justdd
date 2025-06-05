from . import fetch_url, extract_links
import re


def fetch_arch_isos(config):
    isos = []
    base_url = config.get("base_url")
    
    if not base_url:
        error_msg = "fetch_arch_isos: 'base_url' not found in config"
        print(error_msg)
        return [], error_msg
    
    soup, error = fetch_url(base_url, timeout=10, error_prefix="Error fetching Arch Linux main page")
    if error:
        print(f"fetch_arch_isos: {error}")
        return [], error
    
    if not soup:
        error_msg = f"fetch_arch_isos: No soup object from {base_url}"
        print(error_msg)
        return [], error_msg
    
    links_dict = extract_links(soup, base_url)
    
    latest_url = None
    dated_urls = []
    
    for link_text, full_url in links_dict.items():
        if link_text == "latest/":
            latest_url = full_url
            break
        elif re.match(r"\d{4}\.\d{2}\.\d{2}/", link_text):
            dated_urls.append((link_text, full_url))
    
    target_url = latest_url
    if not target_url and dated_urls:
        dated_urls.sort(key=lambda x: x[0], reverse=True)
        target_url = dated_urls[0][1]
    
    if not target_url:
        error_msg = f"fetch_arch_isos: No 'latest/' or dated directories found at {base_url}"
        print(error_msg)
        return [], error_msg
    
    print(f"fetch_arch_isos: Fetching ISOs from {target_url}")
    iso_soup, iso_error = fetch_url(target_url, timeout=10, error_prefix="Error fetching Arch Linux ISO directory")
    if iso_error:
        print(f"fetch_arch_isos: {iso_error}")
        return [], iso_error
    
    if not iso_soup:
        error_msg = f"fetch_arch_isos: No soup object from {target_url}"
        print(error_msg)
        return [], error_msg
    
    iso_links_dict = extract_links(iso_soup, target_url)
    
    for link_text, full_url in iso_links_dict.items():
        if link_text.endswith(".iso"):
            display_name = "ISO"
            
            arch_match = re.search(r"(x86_64|i686)", link_text)
            arch = arch_match.group(1) if arch_match else "unknown"
            
            if "bootstrap" in link_text.lower():
                display_name = f"Bootstrap ({arch})"
            elif "netinstall" in link_text.lower() or "net_" in link_text.lower():
                display_name = f"Net Install ({arch})"
            else:
                date_match = re.search(r"(\d{4}\.\d{2}\.\d{2})", link_text)
                if date_match:
                    date = date_match.group(1)
                    display_name = f"ISO {date} ({arch})"
                else:
                    display_name = f"ISO ({arch})"
            
            isos.append({
                "name": display_name,
                "url": full_url
            })
            print(f"fetch_arch_isos: Found ISO: {display_name} at {full_url}")
    
    if not isos:
        error_msg = f"fetch_arch_isos: No ISO files found in {target_url}"
        print(error_msg)
        return [], error_msg
    
    print(f"fetch_arch_isos: Successfully found {len(isos)} ISO(s)")
    return isos, None
