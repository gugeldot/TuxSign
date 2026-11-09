"""Tema (oscuro/claro), iconos SVG vectoriales y QSS."""
from __future__ import annotations

from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

DARK = dict(
    bg="#0E1016", surface="#161923", surface2="#1E2230", border="#2B3043", text="#E8EAF2",
    muted="#8B91A8", accent="#7C8CFF", accent2="#4FD1C5", danger="#FF6B7A", ok="#4ADE80",
    warn="#FBBF24", viewer="#0A0C11", on_accent="#0B0E1A",
)
LIGHT = dict(
    bg="#F3F4FA", surface="#FFFFFF", surface2="#EEF0F9", border="#DADDEB", text="#1A1D2B",
    muted="#6A7088", accent="#4F5BD5", accent2="#0E9F94", danger="#D93B4F", ok="#16A34A",
    warn="#B7791F", viewer="#E4E6F1", on_accent="#FFFFFF",
)

P: dict[str, str] = dict(DARK)
IS_DARK = True


def set_theme(dark: bool) -> None:
    global IS_DARK
    IS_DARK = dark
    P.clear()
    P.update(DARK if dark else LIGHT)
    _ICON_CACHE.clear()


def mix(a: str, b: str, t: float) -> QColor:
    ca, cb = QColor(a), QColor(b)
    return QColor(
        round(ca.red() + (cb.red() - ca.red()) * t),
        round(ca.green() + (cb.green() - ca.green()) * t),
        round(ca.blue() + (cb.blue() - ca.blue()) * t),
    )


_PATHS = {
    "file": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>',
    "key": '<circle cx="7.5" cy="15.5" r="4.5"/><path d="M10.7 12.3 21 2m-3 3 3 3m-6-0 2.5 2.5"/>',
    "pen": '<path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/>',
    "shield": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><polyline points="9 12 11 14 15 10"/>',
    "check": '<polyline points="20 6 9 17 4 12"/>',
    "trash": '<polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>',
    "undo": '<polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/>',
    "zoom-in": '<circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/><line x1="11" y1="8" x2="11" y2="14"/><line x1="8" y1="11" x2="14" y2="11"/>',
    "zoom-out": '<circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/><line x1="8" y1="11" x2="14" y2="11"/>',
    "fit": '<path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"/>',
    "sun": '<circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>',
    "moon": '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>',
    "upload": '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>',
    "lock": '<rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
    "left": '<polyline points="15 18 9 12 15 6"/>',
    "right": '<polyline points="9 18 15 12 9 6"/>',
    "eye": '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>',
    "x": '<line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>',
    "alert": '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>',
    "globe": '<circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>',
    "info": '<circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>',
    "stamp": '<path d="M5 22h14"/><path d="M19.27 13.73A2.5 2.5 0 0 0 17.5 13h-11A2.5 2.5 0 0 0 4 15.5V17a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-1.5c0-.66-.26-1.3-.73-1.77"/><path d="M14 13V8.5C14 7 15 7 15 5a3 3 0 0 0-3-3c-1.66 0-3 1-3 3s1 2 1 3.5V13"/>',
}
_ICON_CACHE: dict[tuple, QIcon] = {}


def pixmap(name: str, color: str, size: int = 20, dpr: float = 2.0) -> QPixmap:
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" '
        f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{_PATHS[name]}</svg>'
    )
    px = QPixmap(int(size * dpr), int(size * dpr))
    px.fill(Qt.GlobalColor.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    QSvgRenderer(QByteArray(svg.encode())).render(p)
    p.end()
    px.setDevicePixelRatio(dpr)
    return px


def icon(name: str, color: str | None = None, size: int = 20) -> QIcon:
    col = color or P["text"]
    key = (name, col, size)
    if key not in _ICON_CACHE:
        _ICON_CACHE[key] = QIcon(pixmap(name, col, size))
    return _ICON_CACHE[key]


def stylesheet() -> str:
    c = P
    return f"""
* {{ font-family: "Inter", "Noto Sans", "Cantarell", "DejaVu Sans", sans-serif; font-size: 13px; color: {c['text']}; }}
QMainWindow, #root {{ background: {c['bg']}; }}
QToolTip {{ background: {c['surface2']}; color: {c['text']}; border: 1px solid {c['border']}; padding: 6px 8px; border-radius: 8px; }}
#topbar {{ background: {c['surface']}; border-bottom: 1px solid {c['border']}; }}
#logo {{ font-size: 16px; font-weight: 700; letter-spacing: 0.3px; }}
#chip {{ background: {c['surface2']}; border: 1px solid {c['border']}; border-radius: 12px; padding: 4px 12px; color: {c['muted']}; }}
#side {{ background: {c['surface']}; border-left: 1px solid {c['border']}; }}
QScrollArea, QScrollArea > QWidget > QWidget {{ background: transparent; border: none; }}
#card {{ background: {c['surface2']}; border: 1px solid {c['border']}; border-radius: 16px; }}
#cardTitle {{ font-size: 14px; font-weight: 700; }}
#muted {{ color: {c['muted']}; font-size: 12px; }}
#badge {{ background: {c['border']}; color: {c['muted']}; border-radius: 11px; font-weight: 700; font-size: 11px; }}
#h1 {{ font-size: 26px; font-weight: 800; }}
QLineEdit, QPlainTextEdit, QSpinBox {{ background: {c['surface']}; border: 1px solid {c['border']}; border-radius: 10px; padding: 8px 10px; selection-background-color: {c['accent']}; selection-color: {c['on_accent']}; }}
QLineEdit:focus, QPlainTextEdit:focus, QSpinBox:focus {{ border: 1px solid {c['accent']}; }}
QCheckBox {{ spacing: 8px; }}
QCheckBox::indicator {{ width: 18px; height: 18px; border-radius: 6px; border: 1px solid {c['border']}; background: {c['surface']}; }}
QCheckBox::indicator:checked {{ background: {c['accent']}; border: 1px solid {c['accent']}; image: none; }}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: {c['border']}; border-radius: 4px; min-height: 40px; }}
QScrollBar::handle:vertical:hover {{ background: {c['muted']}; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 2px; }}
QScrollBar::handle:horizontal {{ background: {c['border']}; border-radius: 4px; min-width: 40px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
QGraphicsView {{ background: {c['viewer']}; border: none; }}
QDialog {{ background: {c['bg']}; }}
QProgressBar {{ background: transparent; border: none; height: 3px; }}
QProgressBar::chunk {{ background: {c['accent']}; border-radius: 1px; }}
QMessageBox {{ background: {c['bg']}; }}
QMenu {{ background: {c['surface']}; border: 1px solid {c['border']}; border-radius: 12px; padding: 6px; }}
QMenu::item {{ padding: 8px 22px; border-radius: 8px; }}
QMenu::item:selected {{ background: {c['surface2']}; color: {c['accent']}; }}
QComboBox {{ background: {c['surface']}; border: 1px solid {c['border']}; border-radius: 10px; padding: 6px 10px; }}
QComboBox QAbstractItemView {{ background: {c['surface']}; border: 1px solid {c['border']}; selection-background-color: {c['surface2']}; }}
"""
