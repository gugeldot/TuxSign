#!/usr/bin/env python3
"""Comprueba mitigaciones de memoria de los binarios nativos (ELF): canario de pila, PIE, NX, RELRO total, FORTIFY.

Uso: checksec.py [ficheros.so ...]   (sin argumentos: .so de TuxSign y de sus dependencias nativas)
"""
from __future__ import annotations

import glob
import os
import subprocess
import sys


def sh(*a: str) -> str:
    return subprocess.run(a, capture_output=True, text=True).stdout


def check(path: str) -> dict[str, bool]:
    hdr, seg, dyn = sh("readelf", "-h", path), sh("readelf", "-lW", path), sh("readelf", "-d", path)
    syms = sh("readelf", "--dyn-syms", "-W", path)
    return {
        "canary": "__stack_chk_fail" in syms,
        "PIE/ASLR": "DYN" in hdr,
        "NX": "GNU_STACK" in seg and "RWE" not in seg.split("GNU_STACK")[1].split("\n")[0],
        "RELRO": "GNU_RELRO" in seg,
        "BIND_NOW": "BIND_NOW" in dyn or "(FLAGS_1)" in dyn and "NOW" in dyn,
        "FORTIFY": "_chk" in syms.replace("__stack_chk_fail", ""),
    }


def default_targets() -> list[str]:
    import importlib.util as u
    out: list[str] = []
    for mod, pat in (("tuxsign", "tuxsign*.so"), ("pymupdf", "**/*.so"), ("cryptography", "**/*.so"),
                     ("PIL", "*.so"), ("lxml", "*.so"), ("PySide6", "QtCore*.so"), ("PySide6", "Qt/lib/libQt6Core.so*")):
        spec = u.find_spec(mod)
        if spec and spec.submodule_search_locations:
            out += glob.glob(os.path.join(list(spec.submodule_search_locations)[0], pat), recursive=True)
    return sorted({p for p in out if os.path.isfile(p) and not os.path.islink(p)})


if __name__ == "__main__":
    targets = sys.argv[1:] or default_targets()
    cols = ["canary", "PIE/ASLR", "NX", "RELRO", "BIND_NOW", "FORTIFY"]
    print(f"{'binario':44} " + " ".join(f"{c:9}" for c in cols))
    bad = 0
    for t in targets:
        r = check(t)
        bad += not all(r[c] for c in cols[:5])  # FORTIFY no siempre aplica (depende de funciones usadas)
        print(f"{os.path.basename(t)[:44]:44} " + " ".join(f"{'sí' if r[c] else 'NO':9}" for c in cols))
    sys.exit(1 if bad else 0)
