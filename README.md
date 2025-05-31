<div align="center">

<img src="images/icon.png" alt="JustDD - USB Image Writer" width="300">

# JustDD - USB Image Writer

[![Arch Package Build Status](https://img.shields.io/github/actions/workflow/status/xxanqw/justdd/arch-package.yml?label=Arch%20Package&style=for-the-badge)](https://github.com/xxanqw/justdd/actions/workflows/arch-package.yml)
[![Debian Package Build Status](https://img.shields.io/github/actions/workflow/status/xxanqw/justdd/debian-package.yml?label=Debian%20Package&style=for-the-badge)](https://github.com/xxanqw/justdd/actions/workflows/debian-package.yml)
[![Fedora Package Build Status](https://img.shields.io/github/actions/workflow/status/xxanqw/justdd/fedora-package.yml?label=Fedora%20Package&style=for-the-badge)](https://github.com/xxanqw/justdd/actions/workflows/fedora-package.yml)
[![AUR Package Version](https://img.shields.io/aur/version/justdd?style=for-the-badge)](https://aur.archlinux.org/packages/justdd)
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/xxanqw/justdd?style=for-the-badge)](https://github.com/xxanqw/justdd/releases/latest)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue?style=for-the-badge)](https://www.python.org/downloads/)
[![License](https://img.shields.io/github/license/xxanqw/justdd?style=for-the-badge)](LICENSE)

</div>

**JustDD** is a modern, cross-platform USB image writer designed for both beginners and power users. Whether you're creating a Linux live USB or preparing a Windows installer, JustDD provides a safe, intuitive interface with advanced features for professionals.

🎯 **Perfect for:**
- System administrators managing multiple OS installations
- Linux enthusiasts trying new distributions
- IT professionals preparing recovery media
- Anyone who needs reliable USB image writing

## ✨ Features

### 🐧 Linux ISO Support
- **Direct `dd` writing** with real-time progress tracking
- **Verification support** to ensure data integrity
- **Speed optimization** for different USB drive types
- **Automatic drive detection** with safety checks

### 🪟 Windows USB Preparation
- **Intelligent partitioning** (FAT32/NTFS) based on ISO requirements
- **UEFI and Legacy BIOS** boot support
- **Large file handling** (>4GB) with automatic NTFS formatting
- **Boot sector configuration** for maximum compatibility

### 🔧 Advanced Tools
- **Manual Sync Tool**: Force filesystem buffer flush for data integrity
- **Built-in ISO Downloader**: Download popular Linux distributions directly

### 🛡️ Safety & Security
- **Removable drive detection**: Only shows safe target drives
- **Write confirmation**: Multiple confirmation steps prevent accidents
- **Privilege escalation**: Secure `pkexec` integration
- **Process monitoring**: Real-time command output and error handling

### 🎨 User Experience
- **Tabbed interface**: Separate workflows for different OS types
- **Dark theme**: Comfortable viewing in any environment
- **Responsive design**: Works on various screen sizes

## 📷 Screenshots

<div align="center">
   <img src="images/linux.png" alt="Linux ISO tab interface" width="350" />
   <img src="images/windows.png" alt="Windows ISO tab interface" width="350" />
   <img src="images/about.png" alt="About dialog" width="350" />
   <img src="images/iso-downloader.png" alt="ISO Downloader" width="350" />
   <img src="images/sync.png" alt="Sync tool interface" width="350" />
</div>


## 🚀 Quick Start

### 📦 Installation

<details>
<summary><b>🏛️ Arch Linux (Recommended)</b></summary>

```bash
# Using yay (AUR helper)
yay -S justdd

# Or using paru
paru -S justdd

# Manual AUR installation
git clone https://aur.archlinux.org/justdd.git
cd justdd
makepkg -si
```
</details>

<details>
<summary><b>📦 Debian/Ubuntu</b></summary>

Download the latest `.deb` package from the [releases page](https://github.com/xxanqw/justdd/releases/latest):

```bash
# Download and install
wget https://github.com/xxanqw/justdd/releases/latest/download/justdd_*.deb
sudo dpkg -i justdd_*.deb

# Fix dependencies if needed
sudo apt-get install -f
```

**Dependencies included:** `ntfs-3g`, `parted`, `rsync`, and other required tools.
</details>

<details>
<summary><b>🎩 Fedora/CentOS/RHEL</b></summary>

Download the latest `.rpm` package from the [releases page](https://github.com/xxanqw/justdd/releases/latest):

```bash
# Download and install
wget https://github.com/xxanqw/justdd/releases/latest/download/justdd-*.rpm
sudo rpm -i justdd-*.rpm

# Or using dnf
sudo dnf install justdd-*.rpm
```
</details>

<details>
<summary><b>🔧 Other Distributions (From Source)</b></summary>

**Prerequisites:**
- Python 3.9+ 
- Git
- UV package manager

```bash
# Install UV package manager
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc

# Clone and setup
git clone https://github.com/xxanqw/justdd.git
cd justdd
uv venv
source .venv/bin/activate
uv sync

# Launch JustDD
python app.py
```
</details>

### 🎯 Basic Usage

**🐧 Writing Linux ISOs:**
1. Launch JustDD
2. Select the **Linux** tab
3. Click **"Browse..."** to select your ISO file
4. Choose your target USB drive from the dropdown
5. Click **"Write to Drive"** and confirm the operation
6. Wait for completion and verification

**🪟 Preparing Windows USBs:**
1. Select the **Windows** tab  
2. Click **"Browse..."** to select your Windows ISO
3. Choose your target USB drive
4. Click **"Prepare USB"** and confirm
5. JustDD will automatically handle partitioning and file copying

**🔄 Using the Sync Tool:**
- Click **"Sync Tool"** to manually flush write buffers
- Useful before safely removing USB drives
- Ensures all data is properly written to storage

**📥 ISO Downloader:**
- Click **"ISO Downloader"** to browse and download Linux distributions
- Supports major distributions: Ubuntu, Fedora, Debian, Arch, and more
- Downloads directly to your preferred location

## 📋 System Requirements

### Minimum Requirements
- **OS**: Linux (any modern distribution)
- **Python**: 3.9 or newer
- **RAM**: 512 MB available
- **Storage**: 100 MB free space
- **Privileges**: Ability to run `pkexec`

### Required System Tools
JustDD requires these command-line tools (usually pre-installed):

| Tool | Purpose | Usually found in |
|------|---------|------------------|
| `dd` | Raw disk writing | `coreutils` |
| `lsblk` | Block device listing | `util-linux` |
| `parted` | Disk partitioning | `parted` |
| `mkfs.vfat` | FAT32 formatting | `dosfstools` |
| `mkfs.ntfs` | NTFS formatting | `ntfs-3g` |
| `rsync` | File synchronization | `rsync` |
| `mount`/`umount` | Filesystem mounting | `util-linux` |
| `wipefs` | Filesystem signature removal | `util-linux` |
| `pkexec` | Privilege escalation | `polkit` |

### Python Dependencies
- **PySide6**: Qt6 bindings for Python
- **requests**: HTTP library for ISO downloads
- **beautifulsoup4**: HTML parsing for distribution websites
- **qt-material**: Material Design themes

> **📝 Note**: Package installations automatically handle all dependencies.

## 🔨 Development & Building

### Development Setup

```bash
# Clone the repository
git clone https://github.com/xxanqw/justdd.git
cd justdd

# Setup development environment
uv venv
source .venv/bin/activate
uv sync

# Run in development mode
python app.py
```

### Building Standalone Executable

JustDD uses PyInstaller to create portable executables:

```bash
# Install build dependencies
uv sync --all-extras

# Build single-file executable
uv run pyinstaller --onefile \
    --add-data "images/icon.png:images" \
    --name justdd \
    app.py

# Move executable to project root
mv dist/justdd ./

# The executable is now ready for distribution
./justdd
```

### Building Packages

<details>
<summary><b>🏛️ Building Arch Package</b></summary>

```bash
# Update PKGBUILD version if needed
makepkg -si

# Or for AUR submission
makepkg --printsrcinfo > .SRCINFO
```
</details>

<details>
<summary><b>📦 Building Debian Package</b></summary>

```bash
# Debian packaging requires manual setup
# Create debian/ directory structure and build with debuild
# See Debian packaging documentation for details
```
</details>

<details>
<summary><b>🎩 Building RPM Package</b></summary>

```bash
# RPM packaging requires manual setup
# Create .spec file and build with rpmbuild
# See RPM packaging documentation for details
```
</details>

## 🔒 Security & Safety

### Security Model
- **Privilege Separation**: JustDD runs as a regular user and only elevates privileges for specific disk operations
- **Safe Command Execution**: All system commands are carefully validated and sanitized
- **Drive Detection**: Only removable drives are shown to prevent accidental system drive overwrites
- **Confirmation Dialogs**: Multiple confirmation steps before any destructive operations

### Best Practices
- **⚠️ Always verify your target drive** before writing - data will be permanently lost
- **🔌 Use quality USB drives** for better reliability and performance  
- **💾 Backup important data** before any disk operations
- **🔄 Verify your ISOs** using checksums when available
- **⏹️ Don't interrupt** the writing process to avoid corrupted drives

### Permissions Required
JustDD requires elevated privileges for:
- Reading/writing raw block devices (`/dev/sdX`)
- Mounting and unmounting filesystems
- Creating and modifying partition tables
- Formatting filesystems

**Why `pkexec`?**
- More secure than `sudo` for GUI applications
- Provides better user feedback and authentication dialogs
- Follows modern Linux security best practices
- Can be configured via PolicyKit rules

## 📄 License

This project is licensed under the **GNU General Public License v3.0** - see the [LICENSE](LICENSE) file for details.

### What this means:
- ✅ **Free to use** for any purpose
- ✅ **Free to modify** and distribute
- ✅ **Free to distribute** your modifications
- ❗ **Must keep the same license** for derivatives
- ❗ **Must provide source code** for distributed binaries
- ❗ **Must include license notice** in distributions

## 🔗 Links & Resources

### 📦 Downloads & Packages
- **[GitHub Releases](https://github.com/xxanqw/justdd/releases/latest)** - Pre-built packages for all distributions
- **[AUR Package](https://aur.archlinux.org/packages/justdd)** - Arch User Repository
- **[GitHub Repository](https://github.com/xxanqw/justdd)** - Source code and development


---

<div align="center">

**Made with ❤️ by xxanqw**

*If JustDD helped you, consider giving it a ⭐ on GitHub!*

[![Star History Chart](https://api.star-history.com/svg?repos=xxanqw/justdd&type=Date)](https://star-history.com/#xxanqw/justdd&Date)

</div>
