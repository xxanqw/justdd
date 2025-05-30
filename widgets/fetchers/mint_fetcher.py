from . import fetch_url, extract_links
import re
from bs4 import BeautifulSoup
import requests


def fetch_mint_versions(config):
    base_url = config["base_url"]
    versions_data = []
    error_msg = ""
    
    soup, error = fetch_url(base_url, timeout=10, error_prefix="Error fetching Linux Mint versions")
    if error:
        return [], error
    
    links = extract_links(soup, base_url)
    
    is_lmde = config.get("type") == "linuxmint_lmde"
    
    version_numbers_str = []
    for link_text in links.keys():
        stripped_link = link_text.strip("/")
        if is_lmde:
            if re.match(r"^\d+/?$", stripped_link):
                version_numbers_str.append(stripped_link)
        else:
            if re.match(r"^\d+\.\d+/?$", stripped_link):
                version_numbers_str.append(stripped_link)

    if is_lmde:
        sorted_versions = sorted(version_numbers_str, key=int, reverse=True)
    else:
        sorted_versions = sorted(
            version_numbers_str,
            key=lambda v: list(map(int, v.split("."))),
            reverse=True,
        )
    
    for version_str in sorted_versions:
        version_page_url = f"{base_url.rstrip('/')}/{version_str}/"
        versions_data.append({
            "name": f"LMDE {version_str}" if is_lmde else f"Linux Mint {version_str}",
            "id": version_str,
            "url": version_page_url 
        })
    
    return versions_data, None


def fetch_mint_isos(config, version_id):
    if not version_id:
        return [], "Invalid version_id provided to fetch_mint_isos"

    base_url = config["base_url"]
    version_page_url = f"{base_url.rstrip('/')}/{version_id}/"

    isos_list = []
    error_msg = ""
    
    soup, error = fetch_url(version_page_url, timeout=10, error_prefix="Error fetching Linux Mint ISOs")
    if error:
        return [], error
    
    is_lmde = config.get("type") == "linuxmint_lmde"
    
    iso_links_map = extract_links(soup, version_page_url)
    
    expected_edition = config.get("edition", "").lower()
    expected_arch_key = config.get("arch", "").lower()

    for display_text, absolute_iso_url in iso_links_map.items():
        if not absolute_iso_url.endswith(".iso"):
            continue

        iso_filename = absolute_iso_url.split('/')[-1].lower()
        
        edition_match = True
        if expected_edition:
            edition_match = expected_edition in iso_filename
        
        arch_match = True
        arch_identifiers = {
            "64bit": ["64bit", "amd64", "x86_64"],
            "32bit": ["32bit", "i386", "x86"]
        }
        if expected_arch_key and expected_arch_key in arch_identifiers:
            arch_match = any(ident in iso_filename for ident in arch_identifiers[expected_arch_key])

        if edition_match and arch_match:
            current_edition_in_name = "unknown"
            if "cinnamon" in iso_filename: current_edition_in_name = "Cinnamon"
            elif "mate" in iso_filename: current_edition_in_name = "MATE"
            elif "xfce" in iso_filename: current_edition_in_name = "Xfce"
            
            current_arch_in_name = "unknown"
            if any(ident in iso_filename for ident in arch_identifiers["64bit"]): current_arch_in_name = "64-bit"
            elif any(ident in iso_filename for ident in arch_identifiers["32bit"]): current_arch_in_name = "32-bit"
            
            name_parts = []
            if is_lmde:
                name_parts.append(f"LMDE {version_id}")
            else:
                name_parts.append(f"Linux Mint {version_id}")
            
            if current_edition_in_name != "unknown":
                name_parts.append(current_edition_in_name)
            elif expected_edition:
                name_parts.append(expected_edition.capitalize())

            if current_arch_in_name != "unknown":
                name_parts.append(f"({current_arch_in_name})")
            elif expected_arch_key:
                 name_parts.append(f"({expected_arch_key})")
            
            display_name = " ".join(name_parts)
            if not display_name.strip() or display_name.lower().endswith(".iso"):
                display_name = iso_filename

            isos_list.append({
                "name": display_name,
                "url": absolute_iso_url
            })

    if not isos_list:
        error_msg = f"No ISOs found for {config.get('edition', '')} {version_id} at {version_page_url}"
        if not error_msg and iso_links_map:
            for display_text, absolute_iso_url in iso_links_map.items():
                if absolute_iso_url.endswith(".iso"):
                    isos_list.append({"name": f"Generic ISO: {absolute_iso_url.split('/')[-1]}", "url": absolute_iso_url})
                    error_msg = "" 
                    break
    
    return isos_list, error_msg
