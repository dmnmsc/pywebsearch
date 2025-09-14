# Maintainer: dmnmsc
pkgname=pywebsearch-git
pkgver=r73.3fb7e3b
pkgrel=1
pkgdesc="Customizable web search tool with aliases, !bangs and GUI (PyQt6)"
arch=('any')
url="https://github.com/dmnmsc/pywebsearch"
license=('GPL3')
depends=('python' 'python-pyqt6' 'python-pybrowsers')
provides=('pywebsearch')
conflicts=('pywebsearch')
makedepends=('git' 'python-setuptools')
source=("$pkgname::git+https://github.com/dmnmsc/pywebsearch.git")
sha256sums=('SKIP')

pkgver() {
  cd "$srcdir/$pkgname"
  echo "r$(git rev-list --count HEAD).$(git rev-parse --short HEAD)"
}

build() {
  cd "$srcdir/$pkgname"
  python -m build --wheel --no-isolation
}

package() {
  cd "$srcdir/$pkgname"
  python -m installer --destdir="$pkgdir" dist/*.whl

  cp -r resources/linux_icons/* "$pkgdir/usr/share/icons/hicolor/"

  install -Dm644 resources/pywebsearch.png \
    "$pkgdir/usr/share/icons/hicolor/48x48/apps/pywebsearch.png"
}
