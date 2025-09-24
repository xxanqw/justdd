#!/bin/bash

# Example workflow demonstrating the complete JustDD packaging process
# This shows how uv, PyInstaller, and cross-distribution packaging work together

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
source "$SCRIPT_DIR/common.sh"

echo "=================================================="
echo "JustDD Complete Packaging Workflow Example"
echo "=================================================="
echo ""

# Step 1: Display project information
log_info "Step 1: Project Information"
echo "Project: JustDD - USB Image Writer"
echo "Version: $(get_version)"
echo "Distribution: $(detect_distro)"
echo ""

# Step 2: Check and install uv
log_info "Step 2: uv Dependency Management Setup"
check_dependencies

# Verify uv installation
log_success "uv version: $(uv --version)"
log_success "Python version: $(python3 --version)"
echo ""

# Step 3: Set up uv virtual environment
log_info "Step 3: Setting up uv Virtual Environment"
if [ ! -d ".venv" ]; then
    setup_uv_venv
else
    log_info "Virtual environment already exists"
fi
echo ""

# Step 4: Install dependencies with uv
log_info "Step 4: Installing Dependencies with uv"
if ! install_uv_dependencies; then
    log_error "Failed to install dependencies"
    exit 1
fi
echo ""

# Step 5: Build application with PyInstaller
log_info "Step 5: Building Application with PyInstaller"
BUILD_DIR="dist"
if ! build_app "$BUILD_DIR" "justdd" ".venv"; then
    log_error "Failed to build application"
    exit 1
fi
echo ""

# Step 6: Test the built application
log_info "Step 6: Testing Built Application"
if ! test_application "$BUILD_DIR/justdd"; then
    log_error "Application test failed"
    exit 1
fi
echo ""

# Step 7: Handle polkit dependencies
log_info "Step 7: Configuring Polkit Dependencies"
bash "$SCRIPT_DIR/handle-polkit.sh"
echo ""

# Step 8: Build packages for current distribution
log_info "Step 8: Building Distribution Packages"
case "$(detect_distro)" in
    "debian"|"ubuntu"|"linuxmint"|"pop")
        log_info "Building Debian package..."
        bash "$SCRIPT_DIR/build-deb.sh"
        ;;
    "fedora"|"centos"|"rhel")
        log_info "Building RPM package..."
        bash "$SCRIPT_DIR/build-rpm.sh"
        ;;
    "arch"|"manjaro"|"endeavouros")
        log_info "Building Arch Linux package..."
        cd "$PROJECT_ROOT"
        makepkg -f
        ;;
    *)
        log_info "Building universal package..."
        bash "$SCRIPT_DIR/build-all.sh"
        ;;
esac
echo ""

# Step 9: Validate packages
log_info "Step 9: Validating Generated Packages"
OUTPUT_DIR="$PROJECT_ROOT/dist"
for package in "$OUTPUT_DIR"/*.{deb,rpm,pkg.tar.zst}; do
    if [ -f "$package" ]; then
        case "$package" in
            *.deb) validate_package "$package" "deb" ;;
            *.rpm) validate_package "$package" "rpm" ;;
            *.pkg.tar.zst) log_info "Arch package: $(basename "$package")" ;;
        esac
    fi
done
echo ""

# Step 10: Generate build report
log_info "Step 10: Generating Build Report"
generate_build_report "$OUTPUT_DIR"
echo ""

# Step 11: Display results
log_success "=================================================="
log_success "WORKFLOW COMPLETED SUCCESSFULLY!"
log_success "=================================================="
echo ""
echo "Generated files:"
echo "- Application binary: $BUILD_DIR/justdd"
echo "- Build report: $OUTPUT_DIR/build-report.txt"
echo ""

if [ -d "$OUTPUT_DIR" ]; then
    echo "Package files:"
    ls -la "$OUTPUT_DIR"/*.{deb,rpm,pkg.tar.zst} 2>/dev/null || echo "No packages found"
    echo ""
fi

echo "Key Features Demonstrated:"
echo "✅ uv for Python dependency management"
echo "✅ PyInstaller for standalone application bundling"
echo "✅ Cross-distribution package building"
echo "✅ Polkit dependency handling"
echo "✅ Comprehensive testing and validation"
echo "✅ Automated build reporting"
echo ""

echo "Next Steps:"
echo "1. Test package installation: sudo dpkg -i dist/*.deb"
echo "2. Run the application: justdd"
echo "3. Check build report: cat dist/build-report.txt"
echo ""

log_success "Example workflow completed successfully!"