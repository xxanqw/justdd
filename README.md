# JustDD

JustDD is a small, focused USB image writer with a simple wizard-style UI. It helps you write Linux and Windows ISO images to USB drives safely and with progress feedback.
[![PyPI Version](https://img.shields.io/pypi/v/justdd.svg)](https://pypi.org/project/justdd)

Note: You can use the app either by running with `uvx` (recommended), `pipx`, or building from source:
- Run with uvx: `uvx justdd`.
- Run with pipx: `pipx run justdd`.
- Build from source: follow the Quick Start below.  

Before running the app, make sure you have the prerequisites installed (described below).

---

## Quick Start

### Prerequisites

| Name | What it does | Where to obtain |
|---|---|---|
| Python 3.9 or higher | - | Linux got it by default |
| uv or pipx | Allows to run the app without installing it or building from source | [astral.sh (uv)](https://docs.astral.sh/uv/getting-started/installation/) or [pipx.pypa.io](https://pipx.pypa.io/stable/installation/) |
| polkit (policykit-1 on Ubuntu/Debian) | Allows safe root access | Your distribution's package manager, usually pre-installed |
| rsync | Allows to copy files without syncing file system after copying is done | Your distribution's package manager, usually pre-installed |
| libcdio | Allows to read CD/DVD images | Your distribution's package manager, usually pre-installed |
| Windows specific packages (optional)| If you want to install Windows images, you need to install the following packages, if not app still will work for Linux images | - |
| ms-sys | Allows to write Microsoft-compatible boot records for MBR (optional) | [Fedora (RPM Sphere)](https://rpmsphere.github.io/), [Arch (AUR)](https://aur.archlinux.org/packages/ms-sys/), [Ubuntu/Debian (only building from source)](https://sourceforge.net/projects/ms-sys/) |
| ntfs-3g | Allows to read/write NTFS filesystems (optional) | Your distribution's package manager, usually pre-installed |

### Run via uvx (Recommended and the best way)
```sh
uvx justdd
```
(Thanks to @Technetium1 for configuring `uvx`.)

### Run via pipx (Also recommended)
```sh
pipx run justdd
```

### Build and run
Using UV (recommended):
```sh
git clone https://github.com/xxanqw/justdd.git
cd justdd
uv run justdd
```

Or using a plain venv + pip:
```sh
python -m venv .venv
source .venv/bin/activate
pip install -e .
python -m justdd
```

Other methods were deprecated. As i didn't figure out how to properly package DEB and RPM packages. lul

---

## Basic Usage

1. Select an ISO file.
2. Choose the target removable drive.
    * Choose partitioning options (e.g., GPT, MBR) if flashing Windows.
3. Confirm and Flash.

Important: Flashing will overwrite the target drive. Always double-check the selected device.

## Capabilities

| Capability | What it does |
|---|---|
| ISO writing (raw) | Write ISO images directly to removable drives (dd-style) with progress and status. |
| Windows support | Prepare Windows installer drives (partitioning and file handling). |
| Drive detection | Show removable drives only to reduce the risk of selecting system drives. |
| Live logs | View detailed operation logs for troubleshooting. |
| Safe cancellation | Cancel operations with best-effort cleanup and warnings. |
| Notifications | Desktop notifications on completion or failure. |

> [!NOTE]  
> ISO Downloader was removed from the project due to its complexity and lack of enthusiasm.  
> But you can implement it yourself if you want. (will appreciate this)

---

## Contributing & Support

Contributions and bug reports are welcome — open an issue or submit a PR on GitHub.