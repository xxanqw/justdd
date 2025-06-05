from . import fetch_url
import re
import os


def fetch_endeavouros_isos(config):
    isos = []
    base_url = config.get("base_url")

    if not base_url:
        error_msg = "fetch_endeavouros_isos: 'base_url' not found in config"
        print(error_msg)
        return [], error_msg

    print(f"EndeavourOS: Starting fetch from base_url: {base_url}")
    soup, error = fetch_url(
        base_url, timeout=15, error_prefix="Error fetching EndeavourOS main page"
    )
    if error:
        print(f"EndeavourOS: Error fetching main page: {error}")
        return [], error
    if not soup:
        error_msg = f"EndeavourOS: No content from main page {base_url}"
        print(error_msg)
        return [], error_msg

    print(f"EndeavourOS: Searching for direct .iso links on {base_url}")
    for a_tag in soup.find_all("a", href=True):
        href = a_tag.get("href")
        if href and href.endswith(".iso") and href.startswith("http"):
            iso_url = href
            iso_filename = os.path.basename(iso_url)

            link_text = a_tag.get_text().strip()

            mirror_host_from_url = ""
            domain_match = re.search(r":\/\/([^\/]+)", iso_url)
            if domain_match:
                raw_domain = domain_match.group(1)
                mirror_host_from_url = re.sub(
                    r"^(www\\.|mirrors\\.|mirror\\.|ftp\\.)",
                    "",
                    raw_domain,
                    flags=re.IGNORECASE,
                )

            chosen_mirror_name = ""
            if (
                link_text
                and link_text.lower() != iso_filename.lower()
                and not any(
                    term in link_text.lower()
                    for term in [
                        "download",
                        "iso",
                        "direct link",
                        "http",
                        iso_filename.split(".")[0].lower(),
                    ]
                )
                and len(link_text) < 60
            ):
                chosen_mirror_name = link_text
            elif mirror_host_from_url:
                chosen_mirror_name = mirror_host_from_url

            display_name = iso_filename
            if chosen_mirror_name:
                if (
                    chosen_mirror_name.lower() not in iso_filename.lower()
                    or chosen_mirror_name == link_text
                ):
                    display_name = f"{iso_filename} ({chosen_mirror_name})"

            is_duplicate = any(existing_iso["url"] == iso_url for existing_iso in isos)
            if not is_duplicate:
                isos.append({"name": display_name, "url": iso_url})
                print(
                    f"EndeavourOS: Found ISO on main page: {iso_url} as '{display_name}'"
                )

    final_isos = []
    seen_urls = set()
    for iso in isos:
        if iso["url"] not in seen_urls:
            final_isos.append(iso)
            seen_urls.add(iso["url"])

    final_isos.sort(key=lambda x: x["name"])

    if final_isos:
        print(
            f"EndeavourOS: Final list of {len(final_isos)} ISOs: {[iso['name'] for iso in final_isos]}"
        )
        return final_isos, None
    else:
        error_msg = f"EndeavourOS: No ISOs found on {base_url}."
        print(error_msg)
        return [], error_msg
