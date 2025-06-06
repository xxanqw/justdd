#!/bin/bash

# Function to detect Linux distribution
detect_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        DISTRO=$ID
    elif [ -f /etc/lsb-release ]; then
        . /etc/lsb-release
        DISTRO=$DISTRIB_ID
    elif [ -f /etc/debian_version ]; then
        DISTRO="debian"
    elif [ -f /etc/fedora-release ]; then
        DISTRO="fedora"
    elif [ -f /etc/centos-release ]; then
        DISTRO="centos"
    elif [ -f /etc/redhat-release ]; then
        DISTRO="rhel"
    elif [ -f /etc/gentoo-release ]; then
        DISTRO="gentoo"
    elif [ -f /etc/SuSE-release ] || [ -f /etc/opensuse-release ]; then
        DISTRO="opensuse"
    elif [ -f /etc/slackware-version ]; then
        DISTRO="slackware"
    elif [ -f /etc/alpine-release ]; then
        DISTRO="alpine"
    elif [ -f /etc/arch-release ]; then
        DISTRO="arch"
    elif [ -f /etc/void-release ]; then
        DISTRO="void"
    else
        DISTRO="unknown"
    fi
    echo $DISTRO
}

# Get the distribution
DISTRO=$(detect_distro)
echo "Detected distribution: $DISTRO"

# Display warning about required dependencies
echo "⚠️ WARNING ⚠️"
echo "This script is intended for systems with the following packages installed:"
echo "- ntfs-3g"
echo "- polkit"
echo "- dosfstools"
echo ""
echo "Press Enter to continue or Ctrl+C to stop..."
read -r < /dev/tty

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "uv is not installed. Installing instructions for $DISTRO:"
    
    case $DISTRO in
        "fedora")
            echo "Run: pip install uv"
            echo "Or: sudo dnf install python3-uv (if available in repositories)"
            ;;
        "arch"|"manjaro"|"endeavouros")
            echo "Run: pip install uv"
            echo "Or: yay -S python-uv (if using AUR also it recommended)"
            ;;
        "debian"|"ubuntu"|"pop"|"linuxmint"|"elementary")
            echo "Run: pip install uv"
            echo "Or: sudo apt install python3-uv (if available in repositories)"
            ;;
        "opensuse"|"suse")
            echo "Run: pip install uv"
            echo "Or: sudo zypper install python3-uv (if available in repositories)"
            ;;
        "centos"|"rhel"|"rocky"|"almalinux")
            echo "Run: pip install uv"
            echo "Or: sudo yum install python3-uv (if available in repositories)"
            ;;
        "gentoo")
            echo "Run: pip install uv"
            echo "Or: sudo emerge --ask dev-python/uv (if available)"
            ;;
        "alpine")
            echo "Run: pip install uv"
            echo "Or: sudo apk add py3-uv (if available)"
            ;;
        "void")
            echo "Run: pip install uv"
            echo "Or: sudo xbps-install -S python3-uv (if available)"
            ;;
        "slackware")
            echo "Run: pip install uv"
            echo "Or check SlackBuilds.org for a uv package"
            ;;
        *)
            echo "Run: pip install uv"
            echo "Alternatively: pipx install uv (if pipx is installed)"
            ;;
    esac
    
    exit 1
else
    echo "uv is installed. Building application..."

    git clone https://github.com/xxanqw/justdd.git

    cd justdd
    
    uv sync --all-extras

    uv run pyinstaller --onefile \
        --add-data "images/icon.png:images" \
        --name justdd \
        app.py

    mv dist/justdd ./

    echo "Build complete. Run ./justdd to start the application."
fi