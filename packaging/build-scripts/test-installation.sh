#!/bin/bash

# Test package installation on target distributions

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
source "$SCRIPT_DIR/common.sh"

# Test function for Debian/Ubuntu
test_debian_installation() {
    local package_file="$1"

    log_info "Testing Debian package installation..."

    if [ ! -f "$package_file" ]; then
        log_error "Package file not found: $package_file"
        return 1
    fi

    # Install package
    log_info "Installing package..."
    sudo dpkg -i "$package_file" || {
        log_warning "dpkg installation failed, trying with apt..."
        sudo apt install -f -y
        sudo dpkg -i "$package_file"
    }

    # Verify installation
    verify_installation

    # Test basic functionality
    test_basic_functionality

    log_success "Debian package test completed successfully"
}

# Test function for RPM-based systems
test_rpm_installation() {
    local package_file="$1"

    log_info "Testing RPM package installation..."

    if [ ! -f "$package_file" ]; then
        log_error "Package file not found: $package_file"
        return 1
    fi

    # Install package
    log_info "Installing package..."
    sudo rpm -i "$package_file" || sudo dnf install -y "$package_file"

    # Verify installation
    verify_installation

    # Test basic functionality
    test_basic_functionality

    log_success "RPM package test completed successfully"
}

# Test function for Arch Linux
test_arch_installation() {
    local package_file="$1"

    log_info "Testing Arch Linux package installation..."

    if [ ! -f "$package_file" ]; then
        log_error "Package file not found: $package_file"
        return 1
    fi

    # Install package
    log_info "Installing package..."
    sudo pacman -U --noconfirm "$package_file"

    # Verify installation
    verify_installation

    # Test basic functionality
    test_basic_functionality

    log_success "Arch Linux package test completed successfully"
}

# Verify installation
verify_installation() {
    log_info "Verifying installation..."

    # Check if binary exists
    if ! command -v justdd &> /dev/null; then
        log_error "justdd binary not found in PATH"
        return 1
    fi

    # Check if desktop file exists
    if [ ! -f "/usr/share/applications/justdd.desktop" ]; then
        log_warning "Desktop file not found"
    fi

    # Check if icon exists
    if [ ! -f "/usr/share/pixmaps/justdd.png" ]; then
        log_warning "Icon file not found"
    fi

    # Check if polkit policy exists
    if [ ! -f "/usr/share/polkit-1/actions/com.github.xxanqw.justdd.policy" ]; then
        log_warning "Polkit policy not found"
    fi

    log_success "Installation verification completed"
}

# Test basic functionality
test_basic_functionality() {
    log_info "Testing basic functionality..."

    # Test version output (if available)
    if justdd --version &> /dev/null; then
        log_success "Version check passed"
    else
        log_info "Version check not available (expected for GUI app)"
    fi

    # Test help output (if available)
    if justdd --help &> /dev/null; then
        log_success "Help check passed"
    else
        log_info "Help check not available (expected for GUI app)"
    fi

    # Check if required system tools are available
    local required_tools=("dd" "parted" "mkfs.vfat" "mkfs.ntfs" "rsync" "mount" "umount")

    for tool in "${required_tools[@]}"; do
        if command -v "$tool" &> /dev/null; then
            log_success "$tool is available"
        else
            log_warning "$tool is not available"
        fi
    done

    log_success "Basic functionality test completed"
}

# Test polkit integration
test_polkit_integration() {
    log_info "Testing polkit integration..."

    # Check if polkit service is running
    if command -v systemctl &> /dev/null; then
        if systemctl is-active --quiet polkit.service 2>/dev/null || systemctl is-active --quiet polkit 2>/dev/null; then
            log_success "Polkit service is running"
        else
            log_warning "Polkit service is not running"
        fi
    fi

    # Check if pkexec is available
    if command -v pkexec &> /dev/null; then
        log_success "pkexec is available"
    else
        log_error "pkexec is not available - privilege escalation will fail"
        return 1
    fi

    log_success "Polkit integration test completed"
}

# Main test function
run_tests() {
    local package_type="$1"
    local package_file="$2"

    if [ -z "$package_file" ]; then
        log_error "No package file specified"
        echo "Usage: $0 <package_type> <package_file>"
        echo "Package types: deb, rpm, arch"
        exit 1
    fi

    log_info "Starting installation tests for $package_type package: $package_file"

    # Test polkit before installation
    test_polkit_integration

    # Run package-specific tests
    case "$package_type" in
        "deb")
            test_debian_installation "$package_file"
            ;;
        "rpm")
            test_rpm_installation "$package_file"
            ;;
        "arch")
            test_arch_installation "$package_file"
            ;;
        *)
            log_error "Unknown package type: $package_type"
            echo "Supported types: deb, rpm, arch"
            exit 1
            ;;
    esac

    # Final polkit test
    test_polkit_integration

    log_success "All tests completed successfully!"
}

# Show usage if no arguments provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <package_type> <package_file>"
    echo ""
    echo "Package types:"
    echo "  deb   - Debian/Ubuntu package (.deb)"
    echo "  rpm   - RPM package (.rpm)"
    echo "  arch  - Arch Linux package (.pkg.tar.zst)"
    echo ""
    echo "Examples:"
    echo "  $0 deb ./dist/justdd_0.1.5-1_amd64.deb"
    echo "  $0 rpm ./dist/justdd-0.1.5-1.noarch.rpm"
    echo "  $0 arch ./dist/justdd-0.1.5-1-x86_64.pkg.tar.zst"
    exit 1
fi

# Run tests
run_tests "$@"