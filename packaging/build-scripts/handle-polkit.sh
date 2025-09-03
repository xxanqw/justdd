#!/bin/bash

# Handle polkit dependency differences across distributions

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
source "$SCRIPT_DIR/common.sh"

# Function to detect polkit package name
detect_polkit_package() {
    local distro="$1"

    case "$distro" in
        "debian"|"ubuntu"|"linuxmint"|"pop"|"elementary")
            echo "policykit-1"
            ;;
        "fedora"|"centos"|"rhel"|"ol")
            echo "polkit"
            ;;
        "opensuse"|"opensuse-leap"|"opensuse-tumbleweed")
            echo "polkit"
            ;;
        "arch"|"manjaro"|"endeavouros"|"garuda")
            echo "polkit"
            ;;
        *)
            # Fallback: try to detect by checking what packages are available
            if command -v apt &> /dev/null; then
                if apt list --installed policykit-1 2>/dev/null | grep -q policykit-1; then
                    echo "policykit-1"
                else
                    echo "polkit"
                fi
            elif command -v dnf &> /dev/null || command -v yum &> /dev/null; then
                echo "polkit"
            elif command -v pacman &> /dev/null; then
                echo "polkit"
            else
                log_warning "Could not detect polkit package, using 'polkit' as default"
                echo "polkit"
            fi
            ;;
    esac
}

# Function to check if polkit is installed and working
check_polkit_status() {
    log_info "Checking polkit status..."

    # Check if polkit service is running
    if command -v systemctl &> /dev/null; then
        if systemctl is-active --quiet polkit.service 2>/dev/null; then
            log_success "polkit service is running"
        elif systemctl is-active --quiet polkit 2>/dev/null; then
            log_success "polkit service is running"
        else
            log_warning "polkit service may not be running"
            log_info "To start polkit service:"
            log_info "  sudo systemctl enable --now polkit"
        fi
    fi

    # Check if pkexec is available
    if command -v pkexec &> /dev/null; then
        log_success "pkexec is available"
    else
        log_warning "pkexec not found - privilege escalation may not work"
    fi
}

# Function to install polkit if needed
install_polkit_if_needed() {
    local polkit_package="$1"

    log_info "Checking if $polkit_package is installed..."

    if command -v dpkg &> /dev/null; then
        # Debian/Ubuntu
        if ! dpkg -l "$polkit_package" 2>/dev/null | grep -q "^ii"; then
            log_info "Installing $polkit_package..."
            sudo apt update && sudo apt install -y "$polkit_package"
        else
            log_success "$polkit_package is already installed"
        fi
    elif command -v rpm &> /dev/null; then
        # RPM-based systems
        if ! rpm -q "$polkit_package" &> /dev/null; then
            log_info "Installing $polkit_package..."
            sudo dnf install -y "$polkit_package" || sudo yum install -y "$polkit_package"
        else
            log_success "$polkit_package is already installed"
        fi
    elif command -v pacman &> /dev/null; then
        # Arch Linux
        if ! pacman -Q "$polkit_package" &> /dev/null; then
            log_info "Installing $polkit_package..."
            sudo pacman -S --noconfirm "$polkit_package"
        else
            log_success "$polkit_package is already installed"
        fi
    else
        log_warning "Unknown package manager, cannot automatically install polkit"
        log_info "Please manually install $polkit_package for your distribution"
    fi
}

# Function to create polkit policy for JustDD
create_polkit_policy() {
    local polkit_package="$1"
    local policy_file=""

    # Determine policy file location based on polkit package
    if [ "$polkit_package" = "policykit-1" ]; then
        policy_file="/usr/share/polkit-1/actions/com.github.xxanqw.justdd.policy"
    else
        policy_file="/usr/share/polkit-1/actions/com.github.xxanqw.justdd.policy"
    fi

    log_info "Installing polkit policy..."

    # Create policy directory if it doesn't exist
    sudo mkdir -p "$(dirname "$policy_file")"

    # Install policy file
    sudo cp "$PROJECT_ROOT/packaging/debian/com.github.xxanqw.justdd.policy" "$policy_file"

    log_success "Polkit policy installed to $policy_file"
}

# Main function
main() {
    local distro="$(detect_distro)"
    local polkit_package="$(detect_polkit_package "$distro")"

    log_info "Detected distribution: $distro"
    log_info "Using polkit package: $polkit_package"

    # Install polkit if needed
    install_polkit_if_needed "$polkit_package"

    # Check polkit status
    check_polkit_status

    # Create polkit policy
    create_polkit_policy "$polkit_package"

    log_success "Polkit setup completed successfully!"
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi