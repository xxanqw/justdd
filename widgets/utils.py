import os
import re
import sys
from pathlib import Path


def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    # Get the root directory of the application (parent of widgets directory)
    root_dir = os.path.dirname(os.path.dirname(__file__))
    return os.path.join(root_dir, relative_path)


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


def send_notification(title="Notification", message=""):
    try:
        from desktop_notifier import DesktopNotifier, Urgency, Icon

        icon_path = Path(resource_path("images/icon.png"))
        icon = Icon(path=icon_path)

        notifier = DesktopNotifier(
            app_name="JustDD", app_icon=icon, notification_limit=10
        )

        # Send notification asynchronously
        import asyncio

        async def send_async_notification():
            await notifier.send(
                title=title,
                message=message,
                urgency=Urgency.Normal,
            )

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(send_async_notification())
            else:
                asyncio.run(send_async_notification())
        except RuntimeError:
            asyncio.run(send_async_notification())

    except ImportError:
        print(f"{title}: {message}")
    except Exception as e:
        print(f"Notification failed: {e}")


def play_notification_sound():
    send_notification("ISO Downloader", "Download completed!")
