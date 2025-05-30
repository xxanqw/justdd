from bs4 import BeautifulSoup
import requests
import re
import traceback
from urllib.parse import urljoin


def fetch_url(url, timeout=15, error_prefix="Error fetching URL"):
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "html.parser"), None
    except requests.exceptions.HTTPError as http_err:
        return None, f"{error_prefix}: HTTP error {http_err}"
    except requests.exceptions.ConnectionError as conn_err:
        return None, f"{error_prefix}: Connection error {conn_err}"
    except requests.exceptions.Timeout as timeout_err:
        return None, f"{error_prefix}: Timeout {timeout_err}"
    except requests.exceptions.RequestException as req_err:
        return None, f"{error_prefix}: Request error {req_err}"
    except Exception as e:
        return None, f"{error_prefix}: {str(e)}"


def extract_links(soup, base_url):
    if not soup:
        return {} 
    
    links_map = {}
    for a in soup.find_all("a", href=True):
        href = a.get("href")
        text = a.get_text().strip()
        if href and text:
            absolute_url = urljoin(base_url, href)
            links_map[text] = absolute_url
    return links_map


# Import all fetchers
from .ubuntu_fetcher import fetch_ubuntu_versions, fetch_ubuntu_isos
from .fedora_fetcher import fetch_fedora_versions, fetch_fedora_isos
from .debian_fetcher import fetch_debian_versions, fetch_debian_isos
from .arch_fetcher import fetch_arch_isos
from .opensuse_fetcher import fetch_opensuse_versions, fetch_opensuse_isos
from .mint_fetcher import fetch_mint_versions, fetch_mint_isos
from .endeavouros_fetcher import fetch_endeavouros_isos
