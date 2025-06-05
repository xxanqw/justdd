from . import fetch_url, extract_links
import re


def fetch_debian_versions(config):
    base_url = config["base_url"]
    versions_data = []
    error_msg = ""

    soup, error = fetch_url(base_url, timeout=10, error_prefix="Error fetching Debian versions")
    if error:
        return [], error

    links = extract_links(soup, base_url)
    
    numeric_versions = []
    for link_text in links.keys():
        stripped_link = link_text.strip("/")
        if re.match(r"^\d+\.\d+(\.\d+)?$", stripped_link):
            numeric_versions.append(stripped_link)

    sorted_versions = sorted(
        numeric_versions,
        key=lambda v: list(map(int, v.split("."))),
        reverse=True,
    )

    for version_str in sorted_versions:
        versions_data.append({
            "name": version_str,
            "id": version_str,
            "url": f"{base_url.rstrip('/')}/{version_str}/"
        })
    
    return versions_data, None


def fetch_debian_isos(config, version_id):
    if not version_id or "Loading" in version_id or "Error" in version_id or "No versions" in version_id:
        return [], f"Invalid version: {version_id}. Please select a valid version."
    
    isos_list = []
    error_msg = ""

    try:
        image_path_segment = config["image_path_template"].format(
            version=version_id, arch=config.get("arch", "amd64")
        )
        iso_page_url = config["base_url"].rstrip("/") + "/" + image_path_segment.lstrip("/")
        iso_page_url = iso_page_url.rstrip("/") + "/"

        soup, error = fetch_url(iso_page_url, timeout=10, error_prefix="Error fetching Debian ISOs")
        if error:
            return [], error
        
        iso_links_map = extract_links(soup, iso_page_url)

        iso_filename_pattern_str = config["iso_filename_pattern"].format(
            arch=config.get("arch", "amd64")
        )
        iso_filename_re = re.compile(iso_filename_pattern_str)

        for display_text, absolute_iso_url in iso_links_map.items():
            iso_filename = absolute_iso_url.split('/')[-1]
            if iso_filename_re.match(iso_filename):
                name_to_use = display_text
                if display_text == iso_filename or not display_text.strip():
                    name_to_use = iso_filename

                isos_list.append({
                    "name": name_to_use,
                    "url": absolute_iso_url
                })

        if not isos_list and iso_links_map:
            error_msg = f"No ISOs matched the expected pattern for {version_id} at {iso_page_url}."

        if not isos_list and not error_msg:
            error_msg = f"No downloadable files found for Debian {version_id} at {iso_page_url}."
    
    except Exception as e:
        error_msg = f"Error fetching Debian ISOs for {version_id}: {e}"
    
    return isos_list, error_msg
