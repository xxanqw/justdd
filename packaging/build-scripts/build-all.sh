#!/bin/bash

# Build all package formats for JustDD

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
source "$SCRIPT_DIR/common.sh"

VERSION="$(get_version)"
DISTRO="$(detect_distro)"

log_info "Building JustDD v$VERSION packages for $DISTRO"

# Check if running as root
if check_root; then
    log_warning "Consider running as regular user to avoid permission issues"
fi

# Create output directory
OUTPUT_DIR="$PROJECT_ROOT/dist"
mkdir -p "$OUTPUT_DIR"

# Function to build package based on distribution
build_for_distro() {
    local target_distro="$1"

    case "$target_distro" in
        "debian"|"ubuntu"|"linuxmint"|"pop")
            log_info "Building Debian package..."
            bash "$SCRIPT_DIR/build-deb.sh"
            ;;
        "fedora"|"centos"|"rhel"|"opensuse")
            log_info "Building RPM package..."
            bash "$SCRIPT_DIR/build-rpm.sh"
            ;;
        "arch"|"manjaro"|"endeavouros")
            log_info "Building Arch Linux package..."
            cd "$PROJECT_ROOT"
            makepkg -f
            mv *.pkg.tar.zst "$OUTPUT_DIR/" 2>/dev/null || true
            ;;
        *)
            log_warning "Unknown distribution: $target_distro"
            log_info "Attempting to detect best package format..."

            # Try to detect based on available tools
            if command -v dpkg-buildpackage &> /dev/null; then
                log_info "Found dpkg tools, building Debian package..."
                bash "$SCRIPT_DIR/build-deb.sh"
            elif command -v rpmbuild &> /dev/null; then
                log_info "Found rpm tools, building RPM package..."
                bash "$SCRIPT_DIR/build-rpm.sh"
            elif command -v makepkg &> /dev/null; then
                log_info "Found makepkg, building Arch package..."
                cd "$PROJECT_ROOT"
                makepkg -f
                mv *.pkg.tar.zst "$OUTPUT_DIR/" 2>/dev/null || true
            else
                log_error "No supported packaging tools found"
                log_info "Please install packaging tools for your distribution:"
                log_info "  Debian/Ubuntu: sudo apt install build-essential debhelper devscripts"
                log_info "  Fedora/CentOS: sudo dnf install rpm-build rpmdevtools"
                log_info "  Arch Linux: sudo pacman -S pacman"
                exit 1
            fi
            ;;
    esac
}

# Build for current distribution
build_for_distro "$DISTRO"

# List created packages
log_success "Build completed. Packages:"
ls -la "$OUTPUT_DIR"/*.{deb,rpm,pkg.tar.zst} 2>/dev/null || log_info "No packages found"

log_success "Done"