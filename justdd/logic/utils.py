import os
import re


def format_time_display(seconds: float) -> str:
    try:
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
    except Exception:
        return "--:--:--"


def clean_filename(filename: str, base_prefix: str = "", version: str = "") -> str:
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


def get_default_download_dir() -> str:
    try:
        from PySide6.QtCore import QStandardPaths

        _dl_const = getattr(QStandardPaths, "DownloadLocation", None)
        if _dl_const is not None:
            default_dir = QStandardPaths.writableLocation(_dl_const)
        else:
            default_dir = ""
    except Exception:
        default_dir = ""

    if not default_dir:
        default_dir = os.path.join(os.path.expanduser("~"), "Downloads")

    os.makedirs(default_dir, exist_ok=True)
    return default_dir


def send_notification(title: str = "Notification", message: str = "") -> None:
    try:
        from desktop_notifier import DesktopNotifier, Urgency  # type: ignore

        notifier = DesktopNotifier(app_name="JustDD", notification_limit=10)

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


def play_notification_sound() -> None:
    send_notification("ISO Downloader", "Download completed!")


__all__ = [
    "format_time_display",
    "clean_filename",
    "get_default_download_dir",
    "send_notification",
    "play_notification_sound",
]
