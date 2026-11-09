"""Diálogos: consentimiento inicial (RGPD), privacidad, verificación de firmas y "Acerca de"."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QFileDialog, QHBoxLayout, QLabel, QMessageBox, QSpinBox, QTextBrowser, QVBoxLayout,
)

from .. import APP_NAME, __version__
from ..audit import AuditLog
from ..i18n import LANGUAGES, set_language, tr
from ..privacy import Settings, erase_all, save_settings
from ..security import atomic_write
from ..signer import SigCheck
from .theme import P
from .widgets import AnimatedButton


def _notice_view() -> QTextBrowser:
    tb = QTextBrowser()
    tb.setHtml(tr("privacy_notice"))
    tb.setOpenLinks(False)
    tb.setStyleSheet(f"QTextBrowser {{ background:{P['surface']}; border:1px solid {P['border']}; border-radius:12px; padding:10px; }}")
    return tb


class ConsentDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setModal(True)
        self.resize(580, 600)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 20)
        lay.setSpacing(14)
        top = QHBoxLayout()
        self.h = QLabel(); self.h.setObjectName("h1")
        self.lang = QComboBox()
        for code, name in LANGUAGES:
            self.lang.addItem(name, code)
        self.lang.currentIndexChanged.connect(self._lang)
        top.addWidget(self.h, 1); top.addWidget(self.lang)
        lay.addLayout(top)
        self.view = _notice_view()
        lay.addWidget(self.view, 1)
        self.audit = QCheckBox(); self.audit.setChecked(True)
        self.ack = QCheckBox()
        lay.addWidget(self.audit); lay.addWidget(self.ack)
        row = QHBoxLayout(); row.addStretch()
        self.no = AnimatedButton("", "ghost"); self.ok = AnimatedButton("", "primary", "check")
        self.ok.setEnabled(False)
        self.no.clicked.connect(self.reject); self.ok.clicked.connect(self.accept)
        self.ack.toggled.connect(self.ok.setEnabled)
        row.addWidget(self.no); row.addWidget(self.ok)
        lay.addLayout(row)
        self._retranslate()

    def _lang(self):
        set_language(self.lang.currentData())
        self._retranslate()

    def _retranslate(self):
        self.setWindowTitle(f"{APP_NAME} · {tr('priv_title')}")
        self.h.setText(tr("consent_welcome"))
        self.view.setHtml(tr("privacy_notice"))
        self.audit.setText(tr("consent_audit")); self.ack.setText(tr("consent_ack"))
        self.no.setText(tr("btn_exit")); self.ok.setText(tr("btn_continue"))


class PrivacyDialog(QDialog):
    def __init__(self, settings: Settings, audit: AuditLog, parent=None):
        super().__init__(parent)
        self.s, self.audit = settings, audit
        self.setWindowTitle(tr("priv_title"))
        self.resize(580, 660)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 20)
        lay.setSpacing(12)
        h = QLabel(tr("priv_title")); h.setObjectName("h1")
        lay.addWidget(h)
        lay.addWidget(_notice_view(), 1)
        self.enabled = QCheckBox(tr("priv_audit_on")); self.enabled.setChecked(settings.audit_enabled)
        lay.addWidget(self.enabled)
        row = QHBoxLayout()
        row.addWidget(QLabel(tr("priv_retention")))
        self.days = QSpinBox(); self.days.setRange(30, 730); self.days.setValue(settings.retention_days)
        row.addWidget(self.days); row.addStretch()
        lay.addLayout(row)
        self.status = QLabel(""); self.status.setObjectName("muted"); self.status.setWordWrap(True)
        lay.addWidget(self.status)
        r2 = QHBoxLayout()
        v = AnimatedButton(tr("priv_verify"), "ghost", "shield"); e = AnimatedButton(tr("priv_export"), "ghost", "file")
        v.clicked.connect(self._verify); e.clicked.connect(self._export)
        r2.addWidget(v); r2.addWidget(e)
        lay.addLayout(r2)
        r3 = QHBoxLayout()
        d = AnimatedButton(tr("priv_erase"), "danger", "trash"); d.clicked.connect(self._erase)
        close = AnimatedButton(tr("priv_save"), "primary", "check"); close.clicked.connect(self._save)
        r3.addWidget(d); r3.addStretch(); r3.addWidget(close)
        lay.addLayout(r3)
        self.erased = False

    def _verify(self):
        ok, n = self.audit.verify()
        self.status.setText(tr("priv_chain_ok" if ok else "priv_chain_bad", n=n))

    def _export(self):
        path, _ = QFileDialog.getSaveFileName(self, tr("dlg_export"), "audit.jsonl")
        if path:
            atomic_write(path, self.audit.export_text().encode("utf-8"), 0o600)
            self.audit.log("export")
            self.status.setText(tr("priv_exported"))

    def _erase(self):
        box = QMessageBox(QMessageBox.Icon.Warning, tr("priv_erase_title"), tr("priv_erase_text"),
                          QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, self)
        box.button(QMessageBox.StandardButton.Yes).setText(tr("btn_yes"))
        box.button(QMessageBox.StandardButton.No).setText(tr("btn_no"))
        if box.exec() == QMessageBox.StandardButton.Yes:
            self.audit.log("erase_requested")
            n = erase_all()
            self.erased = True
            self.status.setText(tr("priv_erased", n=n))
            self.accept()

    def _save(self):
        self.s.audit_enabled = self.enabled.isChecked()
        self.s.retention_days = self.days.value()
        self.audit.enabled, self.audit.retention_days = self.s.audit_enabled, self.s.retention_days
        save_settings(self.s)
        self.accept()


class VerifyDialog(QDialog):
    def __init__(self, checks: list[SigCheck], parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("ver_title"))
        self.resize(480, 300)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 20)
        lay.setSpacing(10)
        h = QLabel(tr("ver_title")); h.setObjectName("h1")
        lay.addWidget(h)
        if not checks:
            lay.addWidget(QLabel(tr("ver_none")))
        for c in checks:
            ok = c.intact and c.covers_all
            name = c.signer.replace("<", "&lt;").replace(">", "&gt;")  # el CN proviene del PDF: no es de confianza
            lbl = QLabel(f"{'✔' if ok else '⚠'}  <b>{name}</b><br><span style='color:{P['muted']}'>"
                         f"{tr('ver_ok') if c.intact else tr('ver_modified')}{'' if c.covers_all else tr('ver_later')}</span>")
            lbl.setTextFormat(Qt.TextFormat.RichText)
            lay.addWidget(lbl)
        lay.addWidget(QLabel(f"<span style='font-size:11px'>{tr('ver_trust')}</span>"))
        lay.addStretch()
        b = AnimatedButton(tr("btn_close"), "primary"); b.clicked.connect(self.accept)
        lay.addWidget(b)


class AboutDialog(QDialog):
    def __init__(self, integrity: str, build: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("about_title"))
        self.resize(420, 220)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 20)
        lay.setSpacing(10)
        h = QLabel(APP_NAME); h.setObjectName("h1")
        lay.addWidget(h)
        lay.addWidget(QLabel(f"{tr('about_version')}: <b>{__version__}</b> · {tr('about_build')}: {build}"))
        integ = {"ok": tr("integ_ok"), "dev": tr("integ_dev")}.get(integrity, tr("integ_fail"))
        lay.addWidget(QLabel(f"{tr('about_integrity')}: <b>{integ}</b>"))
        lay.addStretch()
        b = AnimatedButton(tr("btn_close"), "primary"); b.clicked.connect(self.accept)
        lay.addWidget(b)
