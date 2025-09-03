Name:           justdd
Version:        0.1.5
Release:        1%{?dist}
Summary:        Simple graphical USB image writer for Linux and Windows ISOs

License:        GPL-3.0
URL:            https://github.com/xxanqw/justdd
Source0:        %{name}-%{version}.tar.gz

Requires:       file
Requires:       libcdio
Requires:       psmisc
Requires:       polkit
Requires:       coreutils
Requires:       util-linux
Requires:       parted
Requires:       dosfstools
Requires:       ntfs-3g
Requires:       rsync
Requires:       xdg-utils
Requires:       ms-sys

Recommends:     udisks2
Recommends:     gvfs

BuildArch:      noarch

%description
JustDD is a user-friendly graphical application for writing Linux and Windows
ISO images to USB drives. It supports both BIOS and UEFI boot modes and
provides a simple interface for creating bootable USB drives.

Features:
* Support for Linux and Windows ISO images
* GPT and MBR partition schemes
* UEFI and BIOS compatibility
* Progress tracking and error handling
* Cross-platform compatibility

%prep
%setup -q

%build
# Application pre-built with uv and PyInstaller in build-rpm.sh
# No build steps needed here

%install
# Install pre-built binary
install -Dm755 build/%{name} %{buildroot}%{_bindir}/%{name}

# Install desktop file
install -Dm644 %{name}.desktop %{buildroot}%{_datadir}/applications/%{name}.desktop

# Install icon
install -Dm644 images/icon.png %{buildroot}%{_datadir}/pixmaps/%{name}.png

# Install polkit policy
install -Dm644 com.github.xxanqw.%{name}.policy %{buildroot}%{_datadir}/polkit-1/actions/com.github.xxanqw.%{name}.policy

%files
%license LICENSE
%doc README.md SECURITY.md
%{_bindir}/%{name}
%{_datadir}/applications/%{name}.desktop
%{_datadir}/pixmaps/%{name}.png
%{_datadir}/polkit-1/actions/com.github.xxanqw.%{name}.policy

%changelog
* Wed Sep 03 2025 Ivan Potiienko <contact@xxanqw.pp.ua> - 0.1.5-1
- Initial RPM package
- Added support for PyQt6 interface
- Added comprehensive system dependency handling