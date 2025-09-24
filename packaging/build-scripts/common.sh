#!/bin/bash

# Common functions for JustDD packaging (uv-only, simplified)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Ensure uv is available (the only required tooling besides system-level build deps)
check_dependencies() {
    # Ensure common paths are set
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
    
    if ! command -v uv &> /dev/null; then
        log_warning "uv not found. Installing..."
        install_uv
    fi
    log_success "uv available"
}

# Install uv if not available
install_uv() {
    log_info "Installing uv..."
    
    # Try pip3 first as a fallback for environments without internet
    if command -v pip3 &> /dev/null; then
        log_info "Trying pip3 installation first..."
        if pip3 install uv --break-system-packages &> /dev/null; then
            export PATH="$HOME/.local/bin:$PATH"
            if command -v uv &> /dev/null; then
                log_success "uv installed via pip3"
                return 0
            fi
        fi
    fi
    
    # Fall back to official installer
    if command -v curl &> /dev/null; then
        if curl -LsSf https://astral.sh/uv/install.sh | sh; then
            export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
            if command -v uv &> /dev/null; then
                log_success "uv installed via curl"
                return 0
            fi
        fi
    elif command -v wget &> /dev/null; then
        if wget -qO- https://astral.sh/uv/install.sh | sh; then
            export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
            if command -v uv &> /dev/null; then
                log_success "uv installed via wget"
                return 0
            fi
        fi
    fi
    
    log_error "All uv installation methods failed"
    log_info "Please install uv manually:"
    log_info "  pip3 install uv --break-system-packages"
    log_info "  or visit: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
    log_success "uv installed"
}

# Create requirements.txt from pyproject.toml using uv
# (Optional) export requirements if needed externally
create_requirements() {
    [ -f pyproject.toml ] || { log_error "pyproject.toml missing"; return 1; }
    if uv export --format requirements-txt --output-file requirements.txt; then
        log_success "requirements.txt exported"
    else
        log_warning "Failed to export requirements (ignored)"
    fi
}

# Set up uv virtual environment
# Sync dependencies (includes dev extras for pyinstaller)
sync_deps() {
    log_info "Syncing dependencies (with all extras)..."
    uv sync --all-extras
    log_success "Dependencies synced"
}

# Install dependencies with uv
# Deprecated old helper name kept for backward compatibility
install_uv_dependencies() { sync_deps; }

# Build the application with PyInstaller using uv environment
build_app() {
    local output_dir="$1"; shift
    local app_name="${1:-justdd}"
    mkdir -p "$output_dir"
    log_info "Building $app_name (PyInstaller via uv)"
    
    # Check that icon file exists
    if [ ! -f "images/icon.png" ]; then
        log_error "Icon file images/icon.png not found in $(pwd)"
        return 1
    fi
    
    # Ensure pyinstaller import works (installed as dev extra)
    # Use absolute path for the icon to avoid workpath confusion
    local icon_path="$(pwd)/images/icon.png"
    uv run pyinstaller \
        --onefile \
        --add-data "$icon_path:images" \
        --name "$app_name" \
        --distpath "$output_dir" \
        --workpath build \
        --specpath build \
        --log-level INFO \
        app.py
    local binary_path="$output_dir/$app_name"
    [ -f "$binary_path" ] || { log_error "Build failed: binary missing"; return 1; }
    chmod +x "$binary_path"
    log_success "Built binary: $binary_path ($(du -h "$binary_path" | cut -f1))"
}

# Enhanced logging with timestamps
log_debug() {
    echo -e "${BLUE}[DEBUG $(date '+%H:%M:%S')]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR $(date '+%H:%M:%S')]${NC} $1" >&2
}

log_warning() {
    echo -e "${YELLOW}[WARNING $(date '+%H:%M:%S')]${NC} $1" >&2
}

log_info() {
    echo -e "${BLUE}[INFO $(date '+%H:%M:%S')]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS $(date '+%H:%M:%S')]${NC} $1"
}

# Clean build artifacts
clean_build() { rm -rf build dist ./*.spec __pycache__ ./*.egg-info; }

# Get version from constants.py
get_version() {
    python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from constants import __VERSION__
    print(__VERSION__)
except ImportError:
    print('0.1.5')
"
}

# Detect distribution
detect_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        echo "$ID"
    elif [ -f /etc/debian_version ]; then
        echo "debian"
    elif [ -f /etc/redhat-release ]; then
        echo "rhel"
    else
        echo "unknown"
    fi
}

# Check if running as root (for system package installation)
check_root() { [ "$EUID" -eq 0 ]; }

# Validate package integrity
# (Removed verbose validation/tests by user request)
validate_package() { :; }

# Test application functionality
test_application() { :; }

# Generate build report
generate_build_report() { :; }