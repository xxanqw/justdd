#!/bin/bash

# Build Debian package for JustDD

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
source "$SCRIPT_DIR/common.sh"

PACKAGE_NAME="justdd"
VERSION="$(get_version)"
PACKAGE_DIR="${PACKAGE_NAME}_${VERSION}"

log_info "Building Debian package for JustDD v$VERSION"

# Check dependencies
check_dependencies

# Check if Debian packaging tools are available
if ! command -v dpkg-buildpackage &> /dev/null; then
    log_error "dpkg-buildpackage not found. Please install debian packaging tools:"
    log_info "  sudo apt install build-essential debhelper devscripts"
    exit 1
fi

# Create working directory
WORK_DIR="/tmp/justdd-build-deb"
rm -rf "$WORK_DIR"
mkdir -p "$WORK_DIR"
cd "$WORK_DIR"

log_info "Setting up source directory..."

# Copy source files
cp -r "$PROJECT_ROOT"/* .

# Set up uv virtual environment
if ! setup_uv_venv; then
    log_error "Failed to set up uv virtual environment"
    exit 1
fi

# Install dependencies with uv
if ! install_uv_dependencies; then
    log_error "Failed to install dependencies with uv"
    exit 1
fi

# Ensure PyInstaller is available inside the uv-managed venv
log_info "Installing PyInstaller into the uv virtual environment..."
"$WORK_DIR/.venv/bin/python" -m pip install --upgrade pip
"$WORK_DIR/.venv/bin/python" -m pip install pyinstaller

# Create requirements.txt for reference
create_requirements

# Build application with PyInstaller using uv environment
BUILD_DIR="debian/justdd/usr/bin"
if ! build_app "$BUILD_DIR" "$PACKAGE_NAME" ".venv"; then
    log_error "Failed to build application with PyInstaller"
    exit 1
fi

# Create Debian packaging structure
mkdir -p debian/source
echo "3.0 (quilt)" > debian/source/format

# Copy Debian packaging files
cp -r "$PROJECT_ROOT/packaging/debian"/* debian/

# Update debian/rules to use the pre-built binary
cat > debian/rules << 'EOF'
#!/usr/bin/make -f

export PYBUILD_NAME=justdd
export PYBUILD_DISABLE=test

%:
	dh $@

override_dh_auto_build:
	# Application already built with PyInstaller, just ensure it's in place
	@echo "Application pre-built with PyInstaller using uv"

override_dh_auto_install:
	dh_auto_install

	# Install binary (already built)
	install -Dm755 debian/justdd/usr/bin/justdd debian/justdd/usr/bin/justdd

	# Install desktop file
	install -Dm644 justdd.desktop debian/justdd/usr/share/applications/justdd.desktop

	# Install icon
	install -Dm644 images/icon.png debian/justdd/usr/share/pixmaps/justdd.png

	# Install polkit policy
	install -Dm644 com.github.xxanqw.justdd.policy debian/justdd/usr/share/polkit-1/actions/com.github.xxanqw.justdd.policy

override_dh_auto_clean:
	dh_auto_clean
	# Keep the pre-built binary
EOF

# Create changelog if it doesn't exist
if [ ! -f debian/changelog ]; then
    cat > debian/changelog << EOF
justdd (${VERSION}-1) unstable; urgency=medium

  * New upstream release
  * Built with uv and PyInstaller for better dependency management

 -- Ivan Potiienko <contact@xxanqw.pp.ua>  $(date -R)
EOF
fi

# Create compat file
echo "13" > debian/compat

# Copy desktop and policy files
cp "$PROJECT_ROOT/packaging/debian/justdd.desktop" .
cp "$PROJECT_ROOT/packaging/debian/com.github.xxanqw.justdd.policy" .

# Make scripts executable
chmod +x debian/rules

log_info "Building Debian package..."

# Build the package
dpkg-buildpackage -us -uc -b

log_success "Debian package built successfully!"

# Move package to output directory
OUTPUT_DIR="$PROJECT_ROOT/dist"
mkdir -p "$OUTPUT_DIR"

mv ../*.deb "$OUTPUT_DIR/" 2>/dev/null || true

log_info "Package created: $OUTPUT_DIR/${PACKAGE_NAME}_${VERSION}-1_*.deb"

# Clean up
cd "$PROJECT_ROOT"
rm -rf "$WORK_DIR"

log_success "Build completed successfully!"