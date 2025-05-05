# Maintainer: Ivan Potiienko <contact@xxanqw.pp.ua>
pkgname=justdd
pkgver=0.1.0
pkgrel=1
pkgdesc="JustDD - Simple graphical USB image writer for Linux and Windows ISOs"
arch=('any')
url="https://github.com/xxanqw/justdd"
license=('GPL3')
depends=('python' 'python-uv' 'ntfs-3g' 'xdg-utils')
makedepends=('git')
source=("$pkgname::git+$url.git")
md5sums=('SKIP')

build() {
    cd "$srcdir/$pkgname"
    uv venv
    source ./.venv/bin/activate
    uv sync --all-extras
    uv run nuitka --onefile --standalone --enable-plugin=pyside6 \
        --include-data-file=images/icon.png=images/icon.png \
        -o justdd app.py
}

package() {
    cd "$srcdir/$pkgname"
    install -Dm755 justdd "$pkgdir/usr/bin/justdd"
    install -Dm644 "images/icon.png" "$pkgdir/usr/share/pixmaps/justdd.png"
    
    # Create and install a desktop file
    mkdir -p "$pkgdir/usr/share/applications"
    cat > "$pkgdir/usr/share/applications/justdd.desktop" << EOF
[Desktop Entry]
Name=JustDD
Comment=USB Image Writer for Linux and Windows ISOs
Exec=justdd
Icon=justdd
Terminal=false
Type=Application
Categories=Utility;System;
EOF
}