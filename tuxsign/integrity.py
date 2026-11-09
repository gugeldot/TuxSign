"""Verificación de integridad del código instalado (ISO 27002 A.8.32 / A.8.19).

En compilaciones de release, `scripts/release.py sign` genera MANIFEST.json (SHA-256 de cada fichero del
paquete) y MANIFEST.sig (Ed25519). Al arrancar se comprueba la firma y que no falte, sobre ni cambie ningún fichero
(incluye módulos plantados). En builds de desarrollo no hay clave pública incrustada y se informa como "dev".

Límite honesto: un atacante con escritura sobre el paquete podría sustituir también la clave pública. La
protección fuerte es el sistema de ficheros de solo lectura del Flatpak (/app) o la instalación como root.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os

PKG_DIR = os.path.dirname(os.path.abspath(__file__))
SKIP = {"MANIFEST.json", "MANIFEST.sig"}


def _pubkey() -> bytes:
    try:
        from ._pubkey import PUBKEY_B64
    except ImportError:
        return b""
    return base64.b64decode(PUBKEY_B64) if PUBKEY_B64 else b""


def hash_tree(root: str = PKG_DIR) -> dict[str, str]:
    files: dict[str, str] = {}
    for dirpath, dirnames, names in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d != "__pycache__")
        for n in sorted(names):
            full = os.path.join(dirpath, n)
            rel = os.path.relpath(full, root).replace(os.sep, "/")
            if rel in SKIP or n.endswith((".pyc", ".pyo")):
                continue
            with open(full, "rb") as fh:
                files[rel] = hashlib.sha256(fh.read()).hexdigest()
    # build nativo: el paquete compilado es un .so junto al directorio de datos
    parent = os.path.dirname(root)
    for n in sorted(os.listdir(parent)) if os.path.isdir(parent) else []:
        if n.startswith("tuxsign.") and n.endswith(".so"):
            with open(os.path.join(parent, n), "rb") as fh:
                files["@so/" + n] = hashlib.sha256(fh.read()).hexdigest()
    return files


def canonical(manifest: dict) -> bytes:
    return json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()


def verify(root: str = PKG_DIR) -> str:
    """Devuelve 'ok' | 'dev' | 'fail'."""
    pub = _pubkey()
    if not pub:
        return "dev"
    try:
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

        with open(os.path.join(root, "MANIFEST.json"), "rb") as fh:
            raw = fh.read()
        with open(os.path.join(root, "MANIFEST.sig"), "rb") as fh:
            sig = fh.read()
        try:
            Ed25519PublicKey.from_public_bytes(pub).verify(sig, raw)
        except InvalidSignature:
            return "fail"
        manifest = json.loads(raw)
        return "ok" if manifest.get("files") == hash_tree(root) else "fail"
    except Exception:  # noqa: BLE001 - fallo cerrado
        return "fail"
