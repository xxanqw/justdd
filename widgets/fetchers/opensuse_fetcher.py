from . import fetch_url, extract_links
import re


def fetch_opensuse_versions(config):
    versions_data = []
    error_message = None
    distro_type = config.get("type")
    base_url = config.get("base_url")

    if not base_url or not distro_type:
        return [], "Configuration missing base_url or type for openSUSE."

    if distro_type == "opensuse_leap":
        soup, error = fetch_url(
            base_url, timeout=15, error_prefix="Error fetching openSUSE Leap versions"
        )
        if error:
            return [], error

        found_links = extract_links(soup, base_url)
        
        leap_version_numbers = []
        for link_text in found_links.keys():
            processed_text = link_text.strip("/")
            if re.match(r"^\d+\.\d+/?$", processed_text):
                leap_version_numbers.append(processed_text)
        
        sorted_leap_versions = sorted(
            leap_version_numbers,
            key=lambda v: list(map(int, v.split("."))),
            reverse=True,
        )
        
        for version_str in sorted_leap_versions:
            version_page_url = f"{base_url.rstrip('/')}/{version_str}/"
            versions_data.append({
                "name": f"Leap {version_str}",
                "id": version_str,
                "url": version_page_url 
            })
    
    elif distro_type == "opensuse_tumbleweed":
        versions_data.append({
            "name": "Tumbleweed (Current)",
            "id": "current",
            "url": base_url
        })
    else:
        error_message = f"Unknown openSUSE type: {distro_type}"
        
    return versions_data, error_message


def fetch_opensuse_isos(page_url_from_version, item_specific_config, version_dict):
    isos_list = []
    error_message = None

    distro_type = item_specific_config.get("type")
    version_name = version_dict.get("name", "openSUSE")

    if not page_url_from_version or not distro_type:
        return [], "Missing page_url_from_version or distro_type for fetch_opensuse_isos."

    actual_scrape_url = page_url_from_version
    if distro_type == "opensuse_leap":
        iso_path_segment = item_specific_config.get("iso_path_segment", "").strip("/")
        if iso_path_segment:
             actual_scrape_url = f"{page_url_from_version.rstrip('/')}/{iso_path_segment}/"

    soup, error = fetch_url(actual_scrape_url, timeout=15, error_prefix=f"Error fetching openSUSE ISOs from {actual_scrape_url}")
    if error:
        return [], error
    
    all_links_map = extract_links(soup, actual_scrape_url)
    iso_absolute_links_with_text = [] 
    for link_text, abs_url in all_links_map.items():
        if abs_url.endswith(".iso"):
            iso_absolute_links_with_text.append((link_text, abs_url))

    if distro_type == "opensuse_tumbleweed":
        pattern_str = item_specific_config.get("iso_filename_pattern")
        display_name_template = item_specific_config.get("iso_display_name")
        if pattern_str and display_name_template:
            iso_re = re.compile(pattern_str, re.IGNORECASE)
            found_specific_iso = False
            for link_text, iso_abs_url in iso_absolute_links_with_text:
                iso_filename = iso_abs_url.split('/')[-1]
                if iso_re.search(iso_filename):
                    isos_list.append({"name": display_name_template, "url": iso_abs_url})
                    found_specific_iso = True
                    break 
            if not found_specific_iso:
                error_message = f"Specified Tumbleweed ISO pattern '{pattern_str}' not found at {actual_scrape_url}"
        else:
            error_message = "Missing iso_filename_pattern or iso_display_name in config for openSUSE Tumbleweed."
    
    elif distro_type == "opensuse_leap":
        specific_iso_type_key = item_specific_config.get("iso_type_key")
        version_id_str = version_dict.get("id")
        found_specific_iso = False

        if specific_iso_type_key and version_id_str:
            target_pattern_str = f"openSUSE-Leap-{version_id_str}-{specific_iso_type_key}.*\\.iso$"
            target_re = re.compile(target_pattern_str, re.IGNORECASE)

            for link_text, iso_abs_url in iso_absolute_links_with_text:
                iso_filename = iso_abs_url.split('/')[-1]
                if target_re.search(iso_filename):
                    display_name = f"{version_name} ({specific_iso_type_key})"
                    isos_list.append({"name": display_name, "url": iso_abs_url})
                    found_specific_iso = True
                    break 
            
            if not found_specific_iso:
                error_message = f"Specified Leap ISO '{specific_iso_type_key}' for version {version_id_str} not found at {actual_scrape_url}. Searched with pattern: {target_pattern_str}"
        else:
            error_message = "Missing iso_type_key or version_id for openSUSE Leap in configuration or version data."

        if not found_specific_iso and not error_message and iso_absolute_links_with_text:
            pass

    else:
        error_message = f"ISO fetching not implemented for openSUSE type: {distro_type}"

    if not isos_list and not error_message:
        error_message = f"No ISOs found for {version_name} at {actual_scrape_url}. Check link and patterns."
    elif not isos_list and error_message:
        pass 

    return isos_list, error_message
