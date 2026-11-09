#!/usr/bin/env bash
# TuxSign: compilación, empaquetado y auditoría para Linux.
#   ./build.sh run                 ejecutar desde el venv
#   ./build.sh test                tests del núcleo + humo de UI
#   ./build.sh audit               pip-audit (CVE en dependencias) + bandit (SAST)
#   ./build.sh checksec            mitigaciones de memoria (canario, PIE, RELRO, NX) de los binarios nativos
#   ./build.sh bump <major|minor|patch>   subir versión SemVer
#   ./build.sh wheel               wheel firmada (manifiesto Ed25519) para pipx/pip
#   ./build.sh native              tarball con el código COMPILADO a C/.so (Nuitka), sin fuentes .py
#   ./build.sh flatpak             bundle .flatpak sandboxed (recomendado)
set -euo pipefail
cd "$(dirname "$0")"
APP_ID="io.github.tuxsign.TuxSign"
PYVER="${FLATPAK_PYVER:-3.13}"          # versión de Python de io.qt.PySide.BaseApp
ARCH="${FLATPAK_ARCH:-x86_64}"
VERSION="$(python3 scripts/release.py version)"
say() { printf '\033[1;36m==>\033[0m %s\n' "$*"; }
die() { printf '\033[1;31merror:\033[0m %s\n' "$*" >&2; exit 1; }
PY=.venv/bin/python

venv() {
  [ -d .venv ] || python3 -m venv --system-site-packages .venv
  $PY -m pip install -q --upgrade pip
  $PY -m pip install -q -r requirements.txt -r requirements-dev.txt
  $PY -m pip install -q -e . --no-deps
}

# Venv aparte para el build nativo: Nuitka+PySide6 no son fiables con Python >= 3.14 (SystemError en connect()).
NPY=.venv-native/bin/python
nvenv() {
  [ -d .venv-native ] || "${NATIVE_PY:-python3.12}" -m venv .venv-native || die "Necesitas Python 3.12/3.13 (NATIVE_PY=...)"
  $NPY -c 'import sys; sys.exit(sys.version_info >= (3, 14))' || die "El build nativo requiere Python <= 3.13"
  $NPY -m pip install -q --upgrade pip && $NPY -m pip install -q -r requirements.txt nuitka==4.3.5
  $NPY -m pip install -q -e . --no-deps
}

# Copia limpia del paquete + clave pública + id de build (la clave privada NUNCA entra en el stage)
stage() {
  rm -rf build/stage && mkdir -p build/stage
  cp -r tuxsign pyproject.toml README.md build/stage/
  find build/stage -name __pycache__ -prune -exec rm -rf {} +
  rm -f build/stage/tuxsign/MANIFEST.*
  $PY scripts/release.py prepare build/stage/tuxsign
}

case "${1:-help}" in
  run)  venv; exec $PY -m tuxsign "${@:2}" ;;
  test) venv; $PY -W ignore tests/test_core.py; $PY -W ignore tests/smoke_ui.py "${TMPDIR:-/tmp}" ;;
  audit)
    venv; say "pip-audit (vulnerabilidades conocidas)"; .venv/bin/pip-audit -r requirements.txt --strict || true
    say "bandit (análisis estático)"; .venv/bin/bandit -q -r tuxsign -ll ;;
  checksec) venv; $PY scripts/checksec.py ;;
  bump) [ -n "${2:-}" ] || die "uso: ./build.sh bump major|minor|patch"; say "Nueva versión: $($PY scripts/release.py bump "$2")" ;;
  wheel)
    venv; say "Wheel firmada v$VERSION"; stage; $PY scripts/release.py manifest build/stage
    rm -rf dist && mkdir -p dist && (cd build/stage && ../../$PY -m build -q --wheel --outdir ../../dist)
    (cd dist && sha256sum *.whl | tee SHA256SUMS)
    say "Instalar con:  pipx install dist/tuxsign-$VERSION-*.whl" ;;
  native)
    venv; nvenv; say "Compilando a código nativo con Nuitka ($($NPY -V))"
    command -v gcc >/dev/null && command -v patchelf >/dev/null || die "Faltan gcc/patchelf"
    stage; rm -rf build/native; mkdir -p build/native
    # Mitigaciones de memoria del binario propio: canario de pila, FORTIFY, stack-clash, CET, RELRO total, pila no ejecutable
    export CFLAGS="-O2 -fstack-protector-strong -fstack-clash-protection -fcf-protection=full -D_FORTIFY_SOURCE=3 -fPIC"
    export LDFLAGS="-Wl,-z,relro,-z,now,-z,noexecstack"
    (cd build/stage && ../../$NPY -m nuitka --module tuxsign --include-package=tuxsign \
        --output-dir=../native --remove-output --no-pyi-file \
        --python-flag=no_docstrings --python-flag=no_asserts --assume-yes-for-downloads --quiet)
    out="dist/tuxsign-$VERSION-native"; rm -rf "$out" && mkdir -p "$out/lib" "$out/bin"
    cp build/native/tuxsign.*.so "$out/lib/" && strip --strip-all "$out"/lib/tuxsign.*.so
    install -m755 packaging/tuxsign-launcher "$out/bin/tuxsign"
    $PY scripts/release.py manifest "$out/lib"
    tar -C dist -czf "$out.tar.gz" "$(basename "$out")" && sha256sum "$out.tar.gz" | tee "$out.tar.gz.sha256"
    $NPY scripts/checksec.py "$out"/lib/tuxsign.*.so || die "El binario no cumple las mitigaciones esperadas"
    say "Sin .py en $out/lib. Ejecutar: $out/bin/tuxsign   (requiere el mismo Python y las dependencias de requirements.txt)" ;;
  flatpak)
    # flatpak-builder del sistema, o el empaquetado como Flatpak (no requiere root): flatpak install --user flathub org.flatpak.Builder
    if command -v flatpak-builder >/dev/null; then FB=(flatpak-builder)
    elif flatpak info --user org.flatpak.Builder >/dev/null 2>&1; then FB=(flatpak run --user org.flatpak.Builder)
    else die "Falta flatpak-builder (sudo pacman -S flatpak-builder  ó  flatpak install --user flathub org.flatpak.Builder)"; fi
    flatpak remote-list --user | grep -q flathub || flatpak remote-add --user --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
    venv; stage; $PY scripts/release.py manifest build/stage   # firma en el host; /app es de solo lectura en el sandbox
    say "Descargando wheels (cp${PYVER/./}) (PySide6 lo aporta BaseApp)"
    rm -rf build/wheels && mkdir -p build/wheels
    grep -v -i '^pyside6' requirements.txt | grep -v '^#' > build/req-flatpak.in
    $PY -m pip download -q -r build/req-flatpak.in -d build/wheels --only-binary=:all: \
        --platform "manylinux_2_28_${ARCH}" --platform "manylinux2014_${ARCH}" --platform "manylinux_2_17_${ARCH}" --platform any \
        --python-version "$PYVER" --implementation cp
    say "Hashes SHA-256 (instalación con --require-hashes)"
    : > build/flatpak-requirements.txt
    for w in build/wheels/*.whl; do
      n=$(basename "$w" | awk -F- '{print $1"=="$2}')
      printf '%s --hash=sha256:%s\n' "$n" "$(sha256sum "$w" | cut -d' ' -f1)" >> build/flatpak-requirements.txt
    done
    say "Compilando Flatpak"
    "${FB[@]}" --force-clean --user --install-deps-from=flathub --repo=build/repo build/app packaging/flatpak-manifest.json
    mkdir -p dist && flatpak build-bundle build/repo "dist/tuxsign-$VERSION.flatpak" "$APP_ID"
    (cd dist && sha256sum "tuxsign-$VERSION.flatpak" | tee "tuxsign-$VERSION.flatpak.sha256")
    say "Instalar: flatpak install --user dist/tuxsign-$VERSION.flatpak · Ejecutar: flatpak run $APP_ID" ;;
  *) sed -n '2,10p' "$0" ;;
esac
