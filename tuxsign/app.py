"""Punto de entrada de TuxSign."""
from __future__ import annotations

import os
import sys

from . import APP_ID, APP_NAME, __version__


def _build_id() -> str:
    try:
        from ._build import BUILD
        return BUILD
    except ImportError:
        return "dev"


def main() -> int:
    args = sys.argv[1:]
    if args and args[0] in ("--version", "-V"):
        print(f"{APP_NAME} {__version__} ({_build_id()})")
        return 0

    # 1) Intérprete aislado → 2) integridad → 3) hardening, TODO antes de cargar Qt o datos sensibles.
    from .security import ensure_isolated_interpreter, harden_process
    ensure_isolated_interpreter(args)
    from . import integrity
    integ = integrity.verify()
    if integ == "fail":
        from .i18n import set_language, tr
        print(tr("integrity_abort"), file=sys.stderr)
        return 70
    harden_process()

    from PySide6.QtCore import Qt
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtWidgets import QApplication

    from .audit import AuditLog
    from .i18n import set_language
    from .privacy import load_settings, record_consent
    from .ui import theme
    from .ui.dialogs import ConsentDialog
    from .ui.main_window import MainWindow

    QGuiApplication.setDesktopFileName(APP_ID)
    app = QApplication([sys.argv[0]])  # no aceptar opciones arbitrarias de Qt desde argv
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(__version__)

    settings = load_settings()
    set_language(settings.language)  # por defecto: inglés
    scheme = app.styleHints().colorScheme()
    dark = settings.theme == "dark" or (settings.theme == "auto" and scheme != Qt.ColorScheme.Light)
    theme.set_theme(dark)
    app.setStyleSheet(theme.stylesheet())

    if not settings.consented:
        dlg = ConsentDialog()
        if dlg.exec() != ConsentDialog.DialogCode.Accepted:
            return 0
        from .i18n import current
        settings.language = current()
        record_consent(settings, dlg.audit.isChecked())

    audit = AuditLog(settings.audit_enabled, settings.retention_days)
    audit.purge_expired()

    info = {"integrity": integ, "build": _build_id()}
    win = MainWindow(settings, audit, info)
    win.apply_theme(dark)
    win.show()
    pdfs = [a for a in args if a.lower().endswith(".pdf")]
    if pdfs:
        win.open_pdf(pdfs[0])
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
