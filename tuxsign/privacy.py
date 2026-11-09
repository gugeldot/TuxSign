"""Privacidad (RGPD): minimización, transparencia, retención y supresión.

  * Art. 5.1.c  minimización: solo se guardan ajustes y un registro sin datos personales.
  * Art. 5.1.e  limitación del plazo: retención configurable del registro (de 30 a 730 días).
  * Art. 13     transparencia: aviso de privacidad en el primer arranque.
  * Art. 17     supresión: `erase_all()` elimina todos los datos locales.
  * Art. 25/32  privacidad por diseño y seguridad: permisos 0600, sin red, sin telemetría.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass

from .security import atomic_write

CONSENT_VERSION = 1


def _xdg(var: str, fallback: str) -> str:
    base = os.environ.get(var, "")
    if not os.path.isabs(base):  # la spec XDG exige rutas absolutas, y una relativa permitiría escribir en el cwd
        base = os.path.join(os.path.expanduser("~"), fallback)
    return os.path.join(base, "tuxsign")


def config_dir() -> str:
    return _xdg("XDG_CONFIG_HOME", ".config")


def state_dir() -> str:
    return _xdg("XDG_STATE_HOME", ".local/state")


def ensure_private_dir(path: str) -> str:
    os.makedirs(path, mode=0o700, exist_ok=True)
    os.chmod(path, 0o700)
    return path


@dataclass
class Settings:
    consent_version: int = 0
    consent_ts: float = 0.0
    audit_enabled: bool = True
    retention_days: int = 365
    theme: str = "auto"
    language: str = "en"

    @property
    def consented(self) -> bool:
        return self.consent_version >= CONSENT_VERSION


def _settings_path() -> str:
    return os.path.join(config_dir(), "settings.json")


def load_settings() -> Settings:
    try:
        with open(_settings_path(), "r", encoding="utf-8") as fh:
            raw = json.load(fh)
        known = {k: raw[k] for k in Settings.__dataclass_fields__ if k in raw}
        s = Settings(**known)
    except (OSError, ValueError, TypeError):
        return Settings()
    try:
        s.retention_days = max(30, min(730, int(s.retention_days)))
    except (TypeError, ValueError, OverflowError):  # settings.json corrupto no debe impedir arrancar
        s.retention_days = 365
    s.audit_enabled = bool(s.audit_enabled)
    if s.theme not in ("auto", "dark", "light"):
        s.theme = "auto"
    if s.language not in ("en", "es", "fr", "de", "pt"):
        s.language = "en"
    return s


def save_settings(s: Settings) -> None:
    ensure_private_dir(config_dir())
    atomic_write(_settings_path(), json.dumps(asdict(s), indent=2).encode(), 0o600)


def record_consent(s: Settings, audit_enabled: bool) -> None:
    s.consent_version = CONSENT_VERSION
    s.consent_ts = time.time()
    s.audit_enabled = audit_enabled
    save_settings(s)


def _shred(path: str) -> None:
    try:
        size = os.path.getsize(path)
        with open(path, "r+b", buffering=0) as fh:
            fh.write(b"\x00" * size)
            os.fsync(fh.fileno())
    except OSError:
        pass
    try:
        os.unlink(path)
    except OSError:
        pass


def erase_all() -> int:
    """Art. 17: elimina ajustes y registros. Devuelve nº de ficheros borrados.

    Nota: en SSD/CoW la sobrescritura no es garantía forense, así que se recomienda cifrado de disco (A.8.24).
    """
    count = 0
    for d in (state_dir(), config_dir()):
        if not os.path.isdir(d):
            continue
        for name in os.listdir(d):
            p = os.path.join(d, name)
            if os.path.isfile(p) and not os.path.islink(p):
                _shred(p)
                count += 1
        try:
            os.rmdir(d)
        except OSError:
            pass
    return count
