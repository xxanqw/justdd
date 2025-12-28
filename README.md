# JustDD

JustDD is a small, focused USB image writer with a simple wizard-style UI. It helps you write Linux and Windows ISO images to USB drives safely and with progress feedback.

Note: You can use the app either by running with `uvx` (recommended) or building from source:
- Run with uvx: `uvx git+https://github.com/xxanqw/justdd`.
- Build from source: follow the Quick Start below.

---

## Quick Start

### Run via uvx (Recommended and the best way)
```sh
uvx git+https://github.com/xxanqw/justdd
```
(Thanks to @Technetium1 for configuring `uvx`.)

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