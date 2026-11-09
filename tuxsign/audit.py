"""Registro de auditoría con cadena de hashes (ISO 27002 A.8.15 y A.8.17).

Cada entrada incluye el hash de la anterior: cualquier edición o borrado intermedio
rompe la cadena y `verify()` lo detecta. No se registran datos personales (RGPD art. 5.1.c).
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
import time

from .privacy import ensure_private_dir, state_dir

GENESIS = "0" * 64
ALLOWED_EVENTS = {
    "app_start", "consent", "doc_open", "cert_load_ok", "cert_load_fail", "cert_lock",
    "sign_ok", "sign_fail", "verify", "purge", "export", "erase_requested",
}


def doc_fingerprint(data: bytes) -> str:
    """Huella parcial (16 hex). Pseudonimiza el documento sin permitir reconstruirlo."""
    return hashlib.sha256(data).hexdigest()[:16]


class AuditLog:
    def __init__(self, enabled: bool = True, retention_days: int = 365):
        self.enabled = enabled
        self.retention_days = retention_days
        self.path = os.path.join(state_dir(), "audit.log")

    @staticmethod
    def _digest(prev: str, body: dict) -> str:
        blob = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(prev.encode() + blob).hexdigest()

    def _read(self) -> list[dict]:
        try:
            with open(self.path, "r", encoding="utf-8") as fh:
                return [json.loads(line) for line in fh if line.strip()]
        except (OSError, ValueError):
            return []

    def _last_hash(self, fd: int) -> str:
        """Hash de la última entrada leyendo solo la cola (O(1) en vez de reparsear todo el log)."""
        size = os.fstat(fd).st_size
        if size == 0:
            return GENESIS
        os.lseek(fd, max(0, size - 4096), os.SEEK_SET)
        tail = os.read(fd, 4096).splitlines()
        for line in reversed(tail):
            try:
                return json.loads(line)["hash"]
            except (ValueError, KeyError, TypeError):
                continue
        entries = self._read()  # línea muy larga o cola corrupta: caer al método lento
        return entries[-1]["hash"] if entries else GENESIS

    def log(self, event: str, **detail: str | int | bool) -> None:
        if not self.enabled or event not in ALLOWED_EVENTS:
            return
        ensure_private_dir(state_dir())
        fd = os.open(self.path, os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_CLOEXEC, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            prev = self._last_hash(fd)
            body = {"ts": int(time.time()), "event": event, "detail": detail}
            line = json.dumps({**body, "prev": prev, "hash": self._digest(prev, body)}, separators=(",", ":"))
            os.write(fd, (line + "\n").encode())
            os.fsync(fd)
        finally:
            os.close(fd)

    def verify(self) -> tuple[bool, int]:
        """(íntegro, nº de entradas). La primera entrada ancla la cadena tras una purga."""
        entries = self._read()
        prev = entries[0]["prev"] if entries else GENESIS
        for e in entries:
            body = {k: e[k] for k in ("ts", "event", "detail") if k in e}
            if e.get("prev") != prev or e.get("hash") != self._digest(prev, body):
                return False, len(entries)
            prev = e["hash"]
        return True, len(entries)

    def purge_expired(self) -> int:
        """Retención (RGPD 5.1.e): elimina entradas antiguas conservando la verificabilidad."""
        entries = self._read()
        limit = time.time() - self.retention_days * 86400
        keep = [e for e in entries if e.get("ts", 0) >= limit]
        removed = len(entries) - len(keep)
        if removed and keep:
            payload = "".join(json.dumps(e, separators=(",", ":")) + "\n" for e in keep).encode()
            from .security import atomic_write
            atomic_write(self.path, payload, 0o600)
        elif removed:
            try:
                os.unlink(self.path)
            except OSError:
                pass
        if removed:
            self.log("purge", removed=removed)
        return removed

    def export_text(self) -> str:
        return "".join(json.dumps(e, ensure_ascii=False) + "\n" for e in self._read())
