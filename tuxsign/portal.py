"""Archivos arrastrados desde fuera del sandbox (portal de transferencia de archivos de xdg-desktop-portal).

En un Flatpak sin acceso al sistema de archivos, la ruta real que trae un arrastre no se puede abrir. Los gestores
de archivos que lo soportan añaden a la operación una clave del portal, y con ella se piden rutas que sí son legibles.
"""
from __future__ import annotations

KEYS = ("application/vnd.portal.filetransfer", "application/vnd.portal.files")


def portal_key(mime) -> str | None:
    """Clave del portal incluida en un arrastre, si la hay."""
    for fmt in KEYS:
        if mime.hasFormat(fmt):
            key = bytes(mime.data(fmt)).decode("utf-8", "ignore").strip("\x00\r\n ")
            if key:
                return key
    return None


def retrieve_files(key: str) -> list[str]:
    """Pide al portal las rutas accesibles desde el sandbox. Devuelve una lista vacía si algo falla."""
    try:
        from PySide6.QtDBus import QDBusConnection, QDBusInterface

        iface = QDBusInterface("org.freedesktop.portal.Documents", "/org/freedesktop/portal/documents",
                               "org.freedesktop.portal.FileTransfer", QDBusConnection.sessionBus())
        if not iface.isValid():
            return []
        args = iface.call("RetrieveFiles", key, {}).arguments()
        return [str(p) for p in args[0]] if args and isinstance(args[0], (list, tuple)) else []
    except Exception:  # noqa: BLE001 - es una ayuda opcional: si falla, se usa el mensaje de siempre
        return []
