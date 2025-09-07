#!/bin/bash

# Build RPM package for JustDD

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
source "$SCRIPT_DIR/common.sh"

PACKAGE_NAME="justdd"
VERSION="$(get_version)"
PACKAGE_DIR="${PACKAGE_NAME}-${VERSION}"

log_info "Building RPM package for JustDD v$VERSION"

# Check dependencies
check_dependencies

# Check if RPM build tools are available
if ! command -v rpmbuild &> /dev/null; then
    log_error "rpmbuild not found. Please install RPM packaging tools:"
    log_info "  sudo dnf install rpm-build rpmdevtools"
    exit 1
fi

# Create working directory
WORK_DIR="/tmp/justdd-build-rpm"
rm -rf "$WORK_DIR"
mkdir -p "$WORK_DIR"
cd "$WORK_DIR"

log_info "Setting up RPM build environment..."

# Set up RPM build directories
rpmdev-setuptree

# Copy source files to rpmbuild directory under a versioned subdirectory
mkdir -p ~/rpmbuild/SOURCES/${PACKAGE_NAME}-${VERSION}
cp -r "$PROJECT_ROOT"/* ~/rpmbuild/SOURCES/${PACKAGE_NAME}-${VERSION}/

cd ~/rpmbuild/SOURCES/${PACKAGE_NAME}-${VERSION}
sync_deps

# Build application (uv run pyinstaller)
BUILD_DIR="build"
build_app "$BUILD_DIR" "$PACKAGE_NAME"

# Create tarball with pre-built binary
cd ~/rpmbuild/SOURCES
tar czf ${PACKAGE_NAME}-${VERSION}.tar.gz ${PACKAGE_NAME}-${VERSION}

# Copy spec file
cp "$PROJECT_ROOT/packaging/rpm/justdd.spec" ~/rpmbuild/SPECS/

# Create requirements.txt for reference
cd "$PROJECT_ROOT"
create_requirements
cp requirements.txt ~/rpmbuild/SOURCES/

# Copy additional files
cp "$PROJECT_ROOT/packaging/rpm/justdd.desktop" ~/rpmbuild/SOURCES/
cp "$PROJECT_ROOT/packaging/rpm/com.github.xxanqw.justdd.policy" ~/rpmbuild/SOURCES/

log_info "Building RPM package..."

# Build the package
cd ~/rpmbuild/SPECS
rpmbuild -ba justdd.spec

log_success "RPM package built successfully!"

# Move packages to output directory
OUTPUT_DIR="$PROJECT_ROOT/dist"
mkdir -p "$OUTPUT_DIR"

mv ~/rpmbuild/RPMS/noarch/*.rpm "$OUTPUT_DIR/" 2>/dev/null || true
mv ~/rpmbuild/SRPMS/*.src.rpm "$OUTPUT_DIR/" 2>/dev/null || true

log_info "Packages created in: $OUTPUT_DIR/"

# List created packages
ls -la "$OUTPUT_DIR/"*.rpm

# Clean up
cd "$PROJECT_ROOT"
rm -rf "$WORK_DIR"

log_success "Build completed successfully!"