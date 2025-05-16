# GitHub Workflows for JustDD Package Building

This directory contains GitHub Actions workflows for automatically building and releasing packages for different Linux distributions.

## Available Workflows

### Arch Linux Package
- **File:** `arch-package.yml`
- **Function:** Builds a pacman package (.pkg.tar.zst) for Arch Linux
- **Triggered by:** Git tags starting with 'v' (e.g., v0.1.0) or manual dispatch
- **Output:** PKGBUILD-based Arch package added to GitHub Releases

### Debian Package
- **File:** `debian-package.yml`
- **Function:** Builds a Debian package (.deb)
- **Triggered by:** Git tags starting with 'v' (e.g., v0.1.0) or manual dispatch
- **Output:** Debian package added to GitHub Releases

### Fedora Package
- **File:** `fedora-package.yml`
- **Function:** Builds an RPM package for Fedora
- **Triggered by:** Git tags starting with 'v' (e.g., v0.1.0) or manual dispatch
- **Output:** RPM package added to GitHub Releases

## Usage

To trigger these workflows:

1. Create and push a new version tag:
   ```bash
   git tag v0.1.2
   git push origin v0.1.2
   ```

2. Or manually trigger any workflow from the GitHub Actions tab in your repository.

## Notes

- All workflows extract the version from the PKGBUILD file
- Packages are built in CI environments that match their target distribution
- All packages require similar dependencies: ntfs-3g, dosfstools, rsync, and polkit
- Generated packages are automatically attached to the GitHub Release for the tag
