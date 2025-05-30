import os
import re


def format_time_display(seconds):
    if seconds == float("inf") or seconds < 0:
        return "--:--:--"
    if not seconds or seconds < 1:
        return "00:00" if seconds < 3600 else "00:00:00"

    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"


def clean_filename(filename, base_prefix="", version=""):
    if not filename:
        return "download.iso"

    clean_name = (
        filename.replace(" (Official)", "")
        .replace(" Spin", "")
        .replace(" Lab", "")
        .replace(" (amd64)", "")
        .replace(" (x86_64)", "")
        .replace(" (Intel/AMD)", "-intel-amd")
        .replace(" (NVIDIA)", "-nvidia")
        .replace(" (Raspberry Pi 4)", "-rpi4")
        .replace(" ", "-")
        .lower()
    )

    if base_prefix:
        clean_name = base_prefix

    if (
        version
        and "Loading" not in version
        and "Error" not in version
        and "No versions" not in version
    ):
        if "Current Snapshot" in version:
            clean_name = f"{clean_name}-current"
        else:
            clean_name = f"{clean_name}-{version.replace('/', '')}"

    if not clean_name.lower().endswith(".iso"):
        clean_name = f"{clean_name}.iso"

    clean_name = re.sub(r"[^\w\.\-]", "_", clean_name)
    clean_name = (
        clean_name.replace("__", "_").replace("-_", "-").replace("_-", "-").lower()
    )
    clean_name = clean_name.replace("--", "-").replace(".iso.iso", ".iso")

    return clean_name


def get_default_download_dir():
    from PySide6.QtCore import QStandardPaths

    default_dir = QStandardPaths.writableLocation(QStandardPaths.DownloadLocation)
    if not default_dir:
        default_dir = os.path.join(os.path.expanduser("~"), "Downloads")

    os.makedirs(default_dir, exist_ok=True)
    return default_dir
