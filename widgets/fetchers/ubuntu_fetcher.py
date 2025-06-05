from . import fetch_url, extract_links
import re

def fetch_ubuntu_versions(config):
    versions_data = []
    base_url = config.get("base_url")
    if not base_url:
        error_msg = "fetch_ubuntu_versions: 'base_url' not found in config"
        print(error_msg)
        return [], error_msg

    soup, error = fetch_url(base_url, timeout=10, error_prefix=f"Error fetching Ubuntu versions from {base_url}")
    if error:
        print(f"fetch_ubuntu_versions: {error}")
        return [], error
    
    if not soup:
        error_msg = f"fetch_ubuntu_versions: No soup object from {base_url}"
        print(error_msg)
        return [], error_msg

    links_dict = extract_links(soup, base_url)
    
    version_strings = []
    for link_text in links_dict.keys():
        match = re.match(r"^([0-9]+\.[0-9]+(?:\.[0-9]+)?)/?$", link_text.strip('/'))
        if match:
            version_strings.append(match.group(1))

    def version_sort_key(v_str):
        parts = list(map(int, v_str.split('.')))
        return parts + [0] * (3 - len(parts))

    sorted_versions = sorted(list(set(version_strings)), key=version_sort_key, reverse=True)

    if sorted_versions:
        for v_str in sorted_versions:
            versions_data.append({'name': v_str, 'id': v_str})
        return versions_data, None
    else:
        error_msg = f"fetch_ubuntu_versions: No matching version strings found at {base_url}"
        print(error_msg)
        return [], error_msg


def fetch_ubuntu_isos(version_id, config):
    if not version_id or "Loading" in version_id or "Error" in version_id or "No versions" in version_id:
        error_msg = f"fetch_ubuntu_isos: Invalid version_id: {version_id}"
        print(error_msg)
        return [], error_msg

    distro_base_url = config["base_url"]
    iso_extensions = tuple(config.get("extensions", [".iso", ".img.xz"]))
    iso_pattern_str = config.get("pattern")
    iso_pattern = re.compile(iso_pattern_str) if iso_pattern_str else None

    isos_data = []
    
    is_official_ubuntu = "releases.ubuntu.com" in distro_base_url
    
    possible_iso_page_urls = []
    base_version_path = f"{distro_base_url.rstrip('/')}/{version_id}/"

    if is_official_ubuntu:
        possible_iso_page_urls.append(base_version_path)
    else:
        possible_iso_page_urls.append(f"{base_version_path}release/")
        possible_iso_page_urls.append(base_version_path)

    actual_iso_page_url = ""
    soup_isos = None

    for attempt_url in list(dict.fromkeys(possible_iso_page_urls)):
        print(f"fetch_ubuntu_isos: Trying Ubuntu ISO page: {attempt_url}")
        soup, err = fetch_url(attempt_url, timeout=10, error_prefix=f"Error fetching ISOs from {attempt_url}")
        if not err and soup:
            soup_isos = soup
            actual_iso_page_url = attempt_url
            print(f"fetch_ubuntu_isos: Found ISO page at: {actual_iso_page_url}")
            break
        elif err:
            print(f"fetch_ubuntu_isos: Error for {attempt_url}: {err}")

    if not soup_isos:
        error_msg = f"fetch_ubuntu_isos: Could not find ISO listing page for Ubuntu {version_id}. Attempts: {', '.join(possible_iso_page_urls)}"
        print(error_msg)
        return [], error_msg

    links_dict = extract_links(soup_isos, actual_iso_page_url) 

    for name, url in links_dict.items():
        name_lower = name.lower()
        if name_lower.endswith(iso_extensions):
            if iso_pattern:
                if iso_pattern.search(name):
                    isos_data.append({'name': name, 'url': url})
            else:
                isos_data.append({'name': name, 'url': url})
    
    if not isos_data:
        error_msg = f"fetch_ubuntu_isos: No ISOs found matching criteria on {actual_iso_page_url} for extensions {iso_extensions}"
        print(error_msg)
        return [], error_msg

    isos_data.sort(key=lambda x: x['name'])
    return isos_data, None
