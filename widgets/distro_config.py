# Unified configuration for all distributions
DISTRO_CONFIG = {
    # Ubuntu Flavors
    "Ubuntu (Official)": {"type": "ubuntu", "base_url": "https://releases.ubuntu.com/"},
    "Kubuntu": {
        "type": "ubuntu",
        "base_url": "https://cdimage.ubuntu.com/kubuntu/releases/",
    },
    "Xubuntu": {
        "type": "ubuntu",
        "base_url": "https://cdimage.ubuntu.com/xubuntu/releases/",
    },
    "Lubuntu": {
        "type": "ubuntu",
        "base_url": "https://cdimage.ubuntu.com/lubuntu/releases/",
    },
    "Ubuntu Budgie": {
        "type": "ubuntu",
        "base_url": "https://cdimage.ubuntu.com/ubuntu-budgie/releases/",
    },
    "Ubuntu MATE": {
        "type": "ubuntu",
        "base_url": "https://cdimage.ubuntu.com/ubuntu-mate/releases/",
    },
    "Ubuntu Studio": {
        "type": "ubuntu",
        "base_url": "https://cdimage.ubuntu.com/ubuntustudio/releases/",
    },
    "Ubuntu Kylin": {
        "type": "ubuntu",
        "base_url": "https://cdimage.ubuntu.com/ubuntukylin/releases/",
    },
    "Edubuntu": {
        "type": "ubuntu",
        "base_url": "https://cdimage.ubuntu.com/edubuntu/releases/",
    },
    "Ubuntu Cinnamon": {
        "type": "ubuntu",
        "base_url": "https://cdimage.ubuntu.com/ubuntucinnamon/releases/",
    },
    "Ubuntu Unity": {
        "type": "ubuntu",
        "base_url": "https://cdimage.ubuntu.com/ubuntu-unity/releases/",
    },
    # Fedora Main Editions
    # "Fedora Workstation": {
    #     "type": "fedora_main",
    #     "base_url": "https://download.fedoraproject.org/pub/fedora/linux/releases/",
    #     "path_segment": "Workstation",
    #     "name_key": "Workstation",
    # },
    # Arch Linux
    "Arch Linux": {
        "type": "archlinux",
        "base_url": "https://geo.mirror.pkgbuild.com/iso/",
    },
    # Debian
    "Debian Netinstall (amd64)": {
        "type": "debian",
        "base_url": "https://cdimage.debian.org/debian-cd/",
        "image_path_template": "{version}/amd64/iso-cd/",
        "iso_filename_pattern": r"debian-.*?{arch}-netinst\.iso$",
        "arch": "amd64",
        "version_prefix": "",  # e.g. 12.5.0
    },
    "Debian DVD-1 (amd64)": {  # DVD-1 is usually sufficient
        "type": "debian",
        "base_url": "https://cdimage.debian.org/debian-cd/",
        "image_path_template": "{version}/amd64/iso-dvd/",
        "iso_filename_pattern": r"debian-.*?{arch}-DVD-1\.iso$",
        "arch": "amd64",
        "version_prefix": "",
    },
    "Debian Live GNOME (amd64)": {
        "type": "debian",
        "base_url": "https://cdimage.debian.org/debian-cd/",
        "image_path_template": "{version}-live/amd64/iso-hybrid/",  # Note: version-live
        "iso_filename_pattern": r"debian-live-.*?{arch}-gnome.*?\.iso$",
        "arch": "amd64",
        "version_prefix": "",
    },
    "Debian Live KDE (amd64)": {
        "type": "debian",
        "base_url": "https://cdimage.debian.org/debian-cd/",
        "image_path_template": "{version}-live/amd64/iso-hybrid/",
        "iso_filename_pattern": r"debian-live-.*?{arch}-kde.*?\.iso$",
        "arch": "amd64",
        "version_prefix": "",
    },
    # Linux Mint
    "Linux Mint Cinnamon": {
        "type": "linuxmint",
        "base_url": "https://mirrors.kernel.org/linuxmint/stable/",
        "edition": "cinnamon",
        "arch": "64bit",
    },
    "Linux Mint MATE": {
        "type": "linuxmint",
        "base_url": "https://mirrors.kernel.org/linuxmint/stable/",
        "edition": "mate",
        "arch": "64bit",
    },
    "Linux Mint Xfce": {
        "type": "linuxmint",
        "base_url": "https://mirrors.kernel.org/linuxmint/stable/",
        "edition": "xfce",
        "arch": "64bit",
    },
    "Linux Mint LMDE (Cinnamon)": {  # Linux Mint Debian Edition
        "type": "linuxmint_lmde",  # Uses different versioning (e.g., 6 "Faye")
        "base_url": "https://mirrors.kernel.org/linuxmint/debian/",
        "edition": "cinnamon",
        "arch": "64bit",
    },
    # openSUSE
    "openSUSE Leap DVD (x86_64)": {
        "type": "opensuse_leap",
        "base_url": "https://download.opensuse.org/distribution/leap/",
        "iso_type_key": "DVD-x86_64",
        "iso_path_segment": "iso/",
    },
    "openSUSE Leap Netinstall (x86_64)": {
        "type": "opensuse_leap",
        "base_url": "https://download.opensuse.org/distribution/leap/",
        "iso_type_key": "NET-x86_64",
        "iso_path_segment": "iso/",
    },
    "openSUSE Tumbleweed DVD (x86_64)": {
        "type": "opensuse_tumbleweed",
        "base_url": "https://download.opensuse.org/tumbleweed/iso/",
        "iso_filename_pattern": r"openSUSE-Tumbleweed-DVD-x86_64-Current\.iso$",
        "iso_display_name": "DVD Snapshot (x86_64)",
    },
    "openSUSE Tumbleweed Netinstall (x86_64)": {
        "type": "opensuse_tumbleweed",
        "base_url": "https://download.opensuse.org/tumbleweed/iso/",
        "iso_filename_pattern": r"openSUSE-Tumbleweed-NET-x86_64-Current\.iso$",
        "iso_display_name": "Netinstall Snapshot (x86_64)",
    },
    "openSUSE Tumbleweed KDE Live (x86_64)": {
        "type": "opensuse_tumbleweed",
        "base_url": "https://download.opensuse.org/tumbleweed/iso/",
        "iso_filename_pattern": r"openSUSE-Tumbleweed-KDE-Live-x86_64-Current\.iso$",
        "iso_display_name": "KDE Live Snapshot (x86_64)",
    },
    "openSUSE Tumbleweed GNOME Live (x86_64)": {
        "type": "opensuse_tumbleweed",
        "base_url": "https://download.opensuse.org/tumbleweed/iso/",
        "iso_filename_pattern": r"openSUSE-Tumbleweed-GNOME-Live-x86_64-Current\.iso$",
        "iso_display_name": "GNOME Live Snapshot (x86_64)",
    },
    # EndeavourOS - using main website and mirrors
    "EndeavourOS": {
        "type": "endeavouros",
        "base_url": "https://endeavouros.com/",
        "mirrors_path": "#download-mirror-list",
        "mirrors": {
            "main": "https://endeavouros.com/",  # Main site for version detection
            # No geo mirror as it returns 404
        },
    },
}
