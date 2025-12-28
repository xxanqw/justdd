import os
import subprocess
from typing import Dict, Tuple


class ISODetector:
    @staticmethod
    def detect_iso_type(iso_path: str) -> Tuple[str, Dict[str, str]]:
        try:
            try:
                result = subprocess.run(
                    ["file", iso_path], capture_output=True, text=True, timeout=5
                )
                file_output = result.stdout.lower()
            except Exception:
                file_output = ""

            details = {
                "name": "Unknown",
                "version": "Unknown",
                "architecture": "Unknown",
                "size": ISODetector._get_file_size(iso_path),
            }

            filename = os.path.basename(iso_path).lower()

            windows_patterns = [
                "windows",
                "win10",
                "win11",
                "win7",
                "win8",
                "server",
                "msdn",
                "microsoft",
                "office",
            ]

            linux_patterns = [
                "ubuntu",
                "debian",
                "fedora",
                "centos",
                "rhel",
                "opensuse",
                "mint",
                "arch",
                "manjaro",
                "kali",
                "parrot",
                "elementary",
                "zorin",
                "pop",
                "endeavour",
                "garuda",
                "solus",
                "void",
            ]

            for pattern in windows_patterns:
                if pattern in filename:
                    details["name"] = ISODetector._extract_windows_info(filename)
                    return ("windows", details)

            for pattern in linux_patterns:
                if pattern in filename:
                    details["name"] = ISODetector._extract_linux_info(filename)
                    return ("linux", details)

            iso_type, iso_details = ISODetector._examine_iso_contents(iso_path)
            if iso_type != "unknown":
                details.update(iso_details)
                return (iso_type, details)

            if "boot" in file_output:
                if "microsoft" in file_output or "windows" in file_output:
                    details["name"] = "Windows (detected)"
                    return ("windows", details)
                else:
                    details["name"] = "Linux (detected)"
                    return ("linux", details)

            return ("unknown", details)

        except Exception as e:
            return (
                "unknown",
                {
                    "name": "Detection failed",
                    "error": str(e),
                    "size": ISODetector._get_file_size(iso_path),
                },
            )

    @staticmethod
    def _get_file_size(file_path: str) -> str:
        try:
            size_bytes = os.path.getsize(file_path)
            for unit in ["B", "KB", "MB", "GB"]:
                if size_bytes < 1024:
                    return f"{size_bytes:.1f} {unit}"
                size_bytes /= 1024
            return f"{size_bytes:.1f} TB"
        except Exception:
            return "Unknown"

    @staticmethod
    def _extract_windows_info(filename: str) -> str:
        if "win11" in filename or "windows11" in filename:
            return "Windows 11"
        elif "win10" in filename or "windows10" in filename:
            return "Windows 10"
        elif "win8" in filename or "windows8" in filename:
            return "Windows 8"
        elif "win7" in filename or "windows7" in filename:
            return "Windows 7"
        elif "server" in filename:
            return "Windows Server"
        else:
            return "Windows"

    @staticmethod
    def _extract_linux_info(filename: str) -> str:
        distros = {
            "ubuntu": "Ubuntu",
            "debian": "Debian",
            "fedora": "Fedora",
            "centos": "CentOS",
            "mint": "Linux Mint",
            "arch": "Arch Linux",
            "manjaro": "Manjaro",
            "kali": "Kali Linux",
            "opensuse": "openSUSE",
            "elementary": "elementary OS",
            "zorin": "Zorin OS",
            "pop": "Pop!_OS",
        }

        for key, name in distros.items():
            if key in filename:
                return name

        return "Linux"

    @staticmethod
    def _examine_iso_contents(iso_path: str) -> Tuple[str, Dict[str, str]]:
        try:
            result = subprocess.run(
                ["iso-info", "-d", "-i", iso_path],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                output = result.stdout.lower()

                if any(
                    term in output
                    for term in ["microsoft", "windows", "win32", "winnt"]
                ):
                    return ("windows", {"name": "Windows (ISO analysis)"})

                if any(
                    term in output
                    for term in ["linux", "ubuntu", "debian", "fedora", "gnu"]
                ):
                    return ("linux", {"name": "Linux (ISO analysis)"})

            result = subprocess.run(
                ["iso-info", "-l", "-i", iso_path],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                file_list = result.stdout.lower()

                windows_files = [
                    "setup.exe",
                    "autorun.inf",
                    "bootmgr",
                    "sources/install.wim",
                    "sources/install.esd",
                    "sources/boot.wim",
                    "efi/microsoft",
                    "support/tools",
                    "sources/setuphost.exe",
                ]

                windows_matches = sum(
                    1 for wfile in windows_files if wfile in file_list
                )

                if windows_matches >= 2:
                    return ("windows", {"name": "Windows (file analysis)"})

                linux_files = [
                    "vmlinuz",
                    "initrd",
                    "casper/",
                    "live/",
                    "isolinux/",
                    "syslinux/",
                    "boot/grub",
                    "efi/boot/bootx64.efi",
                ]

                linux_matches = sum(1 for lfile in linux_files if lfile in file_list)

                if linux_matches >= 2 and windows_matches == 0:
                    return ("linux", {"name": "Linux (file analysis)"})
                elif windows_matches > 0:
                    return ("windows", {"name": "Windows (file analysis)"})

        except FileNotFoundError:
            try:
                result = subprocess.run(
                    ["isoinfo", "-d", "-i", iso_path],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )

                if result.returncode == 0:
                    output = result.stdout.lower()

                    if any(
                        term in output
                        for term in ["microsoft", "windows", "win32", "winnt"]
                    ):
                        return ("windows", {"name": "Windows (ISO analysis)"})

                    if any(
                        term in output
                        for term in ["linux", "ubuntu", "debian", "fedora", "gnu"]
                    ):
                        return ("linux", {"name": "Linux (ISO analysis)"})
            except FileNotFoundError:
                pass
            except Exception:
                pass
        except Exception:
            pass

        return ("unknown", {})


__all__ = ["ISODetector"]
