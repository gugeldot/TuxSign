#!/usr/bin/env python3
"""Utilidades de release de TuxSign: versionado SemVer, claves y firma de integridad.

  release.py version                      muestra la versión
  release.py bump major|minor|patch       sube versión (+ metainfo + CHANGELOG)
  release.py keygen                       crea la clave de firma Ed25519 (fuera del repo, 0600)
  release.py prepare <pkgdir>             escribe _pubkey.py y _build.py en el paquete a empaquetar
  release.py manifest <installroot>       genera y firma MANIFEST.json/.sig de <installroot>/tuxsign
"""
from __future__ import annotations

import base64
import datetime
import hashlib
import os
import re
import stat
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
INIT = os.path.join(ROOT, "tuxsign", "__init__.py")
KEY = os.environ.get("TUXSIGN_SIGNING_KEY") or os.path.expanduser("~/.config/tuxsign-release/ed25519.pem")


def version() -> str:
    return re.search(r'__version__\s*=\s*"([^"]+)"', open(INIT).read()).group(1)


def bump(part: str) -> str:
    major, minor, patch = (int(x) for x in version().split("."))
    new = {"major": (major + 1, 0, 0), "minor": (major, minor + 1, 0), "patch": (major, minor, patch + 1)}[part]
    new_v = ".".join(map(str, new))
    old_v = version()
    s = open(INIT).read().replace(f'"{old_v}"', f'"{new_v}"', 1)
    open(INIT, "w").write(s)
    today = datetime.date.today().isoformat()
    meta = os.path.join(ROOT, "packaging", "io.github.tuxsign.TuxSign.metainfo.xml")
    m = open(meta).read().replace("<releases>", f'<releases><release version="{new_v}" date="{today}"/>', 1)
    open(meta, "w").write(m)
    cl = os.path.join(ROOT, "CHANGELOG.md")
    c = open(cl).read()
    c = c.replace("## [Unreleased]\n", f"## [Unreleased]\n\n## [{new_v}] - {today}\n", 1) if "## [Unreleased]" in c else c
    open(cl, "w").write(c)
    return new_v


def keygen() -> None:
    from cryptography.hazmat.primitives import serialization as ser
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    if os.path.exists(KEY):
        print(f"La clave ya existe: {KEY}")
        return
    os.makedirs(os.path.dirname(KEY), mode=0o700, exist_ok=True)
    key = Ed25519PrivateKey.generate()
    pem = key.private_bytes(ser.Encoding.PEM, ser.PrivateFormat.PKCS8, ser.NoEncryption())
    fd = os.open(KEY, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as fh:
        fh.write(pem)
    print(f"Clave creada en {KEY} (0600). HAZ COPIA DE SEGURIDAD y no la subas al repositorio.")


def _load_key():
    from cryptography.hazmat.primitives import serialization as ser

    if not os.path.exists(KEY):
        keygen()
    if stat.S_IMODE(os.stat(KEY).st_mode) & 0o077:
        sys.exit(f"Permisos inseguros en {KEY}: debe ser 0600")
    with open(KEY, "rb") as fh:
        return ser.load_pem_private_key(fh.read(), None)


def _pub_b64() -> str:
    from cryptography.hazmat.primitives import serialization as ser

    raw = _load_key().public_key().public_bytes(ser.Encoding.Raw, ser.PublicFormat.Raw)
    return base64.b64encode(raw).decode()


def prepare(pkgdir: str) -> None:
    pub = _pub_b64()
    try:
        commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, cwd=ROOT).stdout.strip()
    except OSError:
        commit = ""
    build = f"{datetime.datetime.now(datetime.timezone.utc):%Y%m%d}" + (f".{commit}" if commit else "")
    open(os.path.join(pkgdir, "_pubkey.py"), "w").write(f'PUBKEY_B64 = "{pub}"\n')
    open(os.path.join(pkgdir, "_build.py"), "w").write(f'BUILD = "{build}"\n')
    print(f"prepare: pubkey fingerprint {hashlib.sha256(base64.b64decode(pub)).hexdigest()[:16]}, build {build}")


def manifest(install_root: str) -> None:
    sys.path.insert(0, ROOT)
    from tuxsign import integrity

    pkg = os.path.join(install_root, "tuxsign")
    os.makedirs(pkg, exist_ok=True)
    for n in integrity.SKIP:
        try:
            os.unlink(os.path.join(pkg, n))
        except FileNotFoundError:
            pass
    man = integrity.canonical({"version": version(), "files": integrity.hash_tree(pkg)})
    with open(os.path.join(pkg, "MANIFEST.json"), "wb") as fh:
        fh.write(man)
    with open(os.path.join(pkg, "MANIFEST.sig"), "wb") as fh:
        fh.write(_load_key().sign(man))
    print(f"manifest: {len(integrity.hash_tree(pkg))} ficheros firmados")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "version":
        print(version())
    elif cmd == "bump":
        print(bump(sys.argv[2]))
    elif cmd == "keygen":
        keygen()
    elif cmd == "prepare":
        prepare(sys.argv[2])
    elif cmd == "manifest":
        manifest(sys.argv[2])
    else:
        sys.exit(__doc__)
