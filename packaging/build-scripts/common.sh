#!/bin/bash

# Common functions for JustDD packaging

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

# Check if required tools are installed
check_dependencies() {
    local deps=("python3" "uv" "pyinstaller")
    local missing=()

    # Check for uv first
    if ! command -v "uv" &> /dev/null; then
        log_warning "uv not found. Installing uv..."
        install_uv
    fi

    # Check other dependencies
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            missing+=("$dep")
        fi
    done

    if [ ${#missing[@]} -ne 0 ]; then
        log_error "Missing required dependencies: ${missing[*]}"
        log_info "Please install them and try again."
        exit 1
    fi

    log_success "All required build dependencies are available"
}

# Install uv if not available
install_uv() {
    log_info "Installing uv package manager..."

    # Try different installation methods
    if command -v curl &> /dev/null; then
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.cargo/bin:$PATH"
    elif command -v wget &> /dev/null; then
        wget -qO- https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.cargo/bin:$PATH"
    else
        log_error "Neither curl nor wget available for uv installation"
        log_info "Please install uv manually: https://github.com/astral-sh/uv"
        exit 1
    fi

    # Verify uv installation
    if ! command -v uv &> /dev/null; then
        log_error "Failed to install uv"
        exit 1
    fi

    log_success "uv installed successfully"
}

# Create requirements.txt from pyproject.toml using uv
create_requirements() {
    log_info "Creating requirements.txt from pyproject.toml using uv..."

    if [ ! -f "pyproject.toml" ]; then
        log_error "pyproject.toml not found in current directory"
        exit 1
    fi

    # Use uv to export dependencies
    if ! uv export --format requirements-txt --output-file requirements.txt; then
        log_warning "uv export failed, falling back to manual extraction..."

        # Fallback: Extract dependencies manually
        python3 -c "
import tomllib
import sys

try:
    with open('pyproject.toml', 'rb') as f:
        data = tomllib.load(f)

    deps = data.get('project', {}).get('dependencies', [])
    optional_deps = data.get('project', {}).get('optional-dependencies', {}).get('dev', [])

    with open('requirements.txt', 'w') as f:
        for dep in deps:
            f.write(dep + '\n')
        for dep in optional_deps:
            f.write(dep + '\n')

    print('requirements.txt created successfully (fallback method)')
except Exception as e:
    print(f'Error creating requirements.txt: {e}', file=sys.stderr)
    sys.exit(1)
    "
    else
        log_success "requirements.txt created successfully with uv"
    fi
}

# Set up uv virtual environment
setup_uv_venv() {
    local venv_path="${1:-.venv}"

    log_info "Setting up uv virtual environment..."

    # Create uv virtual environment
    if ! uv venv "$venv_path"; then
        log_error "Failed to create uv virtual environment"
        return 1
    fi

    log_success "uv virtual environment created at $venv_path"
}

# Install dependencies with uv
install_uv_dependencies() {
    local venv_path="${1:-.venv}"

    log_info "Installing dependencies with uv..."

    # Activate virtual environment and install dependencies
    if ! uv sync --all-extras; then
        log_error "Failed to install dependencies with uv"
        return 1
    fi

    log_success "Dependencies installed successfully with uv"
}

# Build the application with PyInstaller using uv environment
build_app() {
    local output_dir="$1"
    local app_name="${2:-justdd}"
    local venv_path="${3:-.venv}"

    log_info "Building application with PyInstaller using uv environment..."

    # Create output directory
    mkdir -p "$output_dir"

    # Check if virtual environment exists
    if [ ! -d "$venv_path" ]; then
        log_error "Virtual environment not found at $venv_path"
        log_info "Run setup_uv_venv first"
        return 1
    fi

    # Activate virtual environment and build with PyInstaller
    local pyinstaller_cmd="$venv_path/bin/pyinstaller"

    if [ ! -f "$pyinstaller_cmd" ]; then
        log_error "PyInstaller not found in virtual environment"
        log_info "Make sure PyInstaller is installed in the uv environment"
        return 1
    fi

    log_info "Using PyInstaller from: $pyinstaller_cmd"

    # Build with PyInstaller
    if ! "$pyinstaller_cmd" \
        --onefile \
        --add-data "images/icon.png:images" \
        --name "$app_name" \
        --distpath "$output_dir" \
        --workpath "build" \
        --specpath "build" \
        --log-level INFO \
        app.py; then
        log_error "PyInstaller build failed"
        return 1
    fi

    # Verify the binary was created
    local binary_path="$output_dir/$app_name"
    if [ ! -f "$binary_path" ]; then
        log_error "Binary not found at expected location: $binary_path"
        return 1
    fi

    # Make binary executable
    chmod +x "$binary_path"

    log_success "Application built successfully: $binary_path"
    log_info "Binary size: $(du -h "$binary_path" | cut -f1)"
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
clean_build() {
    log_info "Cleaning build artifacts..."

    rm -rf build dist *.spec __pycache__ *.egg-info
    rm -f requirements.txt

    log_success "Build artifacts cleaned"
}

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
check_root() {
    if [ "$EUID" -eq 0 ]; then
        log_warning "Running as root - this may cause permission issues"
        return 0
    else
        return 1
    fi
}

# Validate package integrity
validate_package() {
    local package_file="$1"
    local package_type="$2"

    log_info "Validating $package_type package: $package_file"

    if [ ! -f "$package_file" ]; then
        log_error "Package file not found: $package_file"
        return 1
    fi

    case "$package_type" in
        "deb")
            if command -v dpkg &> /dev/null; then
                log_info "Checking DEB package integrity..."
                dpkg --info "$package_file" > /dev/null
                log_success "DEB package validation passed"
            else
                log_warning "dpkg not available for validation"
            fi
            ;;
        "rpm")
            if command -v rpm &> /dev/null; then
                log_info "Checking RPM package integrity..."
                rpm -qp "$package_file" > /dev/null
                log_success "RPM package validation passed"
            else
                log_warning "rpm not available for validation"
            fi
            ;;
        *)
            log_info "Package type validation not implemented for: $package_type"
            ;;
    esac

    # Check file size
    local size=$(du -h "$package_file" | cut -f1)
    log_info "Package size: $size"
}

# Test application functionality
test_application() {
    local binary_path="$1"

    log_info "Testing application functionality..."

    if [ ! -f "$binary_path" ]; then
        log_error "Binary not found: $binary_path"
        return 1
    fi

    # Check if binary is executable
    if [ ! -x "$binary_path" ]; then
        log_error "Binary is not executable: $binary_path"
        return 1
    fi

    # Try to run binary with --help (if supported)
    if timeout 10s "$binary_path" --help > /dev/null 2>&1; then
        log_success "Application help test passed"
    else
        log_info "Application help test skipped (GUI application)"
    fi

    # Check binary size and type
    local size=$(du -h "$binary_path" | cut -f1)
    log_info "Binary size: $size"

    if command -v file &> /dev/null; then
        local file_info=$(file "$binary_path")
        log_info "Binary type: $file_info"
    fi

    log_success "Application functionality test completed"
}

# Generate build report
generate_build_report() {
    local output_dir="$1"
    local report_file="$output_dir/build-report.txt"

    log_info "Generating build report..."

    {
        echo "JustDD Build Report"
        echo "==================="
        echo "Build Date: $(date)"
        echo "Version: $(get_version)"
        echo "Distribution: $(detect_distro)"
        echo "User: $(whoami)"
        echo ""

        echo "Build Environment:"
        echo "- uv version: $(uv --version 2>/dev/null || echo 'Not found')"
        echo "- Python version: $(python3 --version 2>/dev/null || echo 'Not found')"
        echo "- PyInstaller version: $(pyinstaller --version 2>/dev/null || echo 'Not found')"
        echo ""

        echo "Generated Packages:"
        if [ -d "$output_dir" ]; then
            ls -la "$output_dir"/*.{deb,rpm,pkg.tar.zst} 2>/dev/null || echo "No packages found"
        else
            echo "Output directory not found"
        fi
        echo ""

        echo "Package Details:"
        for package in "$output_dir"/*.{deb,rpm,pkg.tar.zst}; do
            if [ -f "$package" ]; then
                echo "- $(basename "$package"): $(du -h "$package" | cut -f1)"
            fi
        done

    } > "$report_file"

    log_success "Build report generated: $report_file"
}