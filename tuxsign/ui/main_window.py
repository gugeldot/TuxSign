"""Ventana principal: visor + panel de pasos (certificado → bloque de firma → firmar)."""
from __future__ import annotations

import os
from datetime import datetime

from PySide6.QtCore import (
    QBuffer, QByteArray, QEasingCurve, QEvent, QIODevice, QObject, QPropertyAnimation, QRunnable, Qt, QThreadPool,
    QTimer, Signal,
)
from PySide6.QtWidgets import (
    QApplication, QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMenu, QProgressBar, QScrollArea,
    QStackedWidget, QVBoxLayout, QWidget,
)

from .. import APP_NAME
from ..audit import AuditLog, doc_fingerprint
from ..i18n import LANGUAGES, set_language, tr
from ..pdfdoc import PdfDoc
from ..privacy import Settings, save_settings
from ..security import MAX_P12_BYTES, MAX_PDF_BYTES, AttemptLimiter, InputRejected, Secret, atomic_write, read_regular_file
from ..signer import AppError, CertificateError, check_signatures, load_pkcs12, sign_pdf
from . import theme
from .dialogs import AboutDialog, PrivacyDialog, VerifyDialog
from .theme import P
from .viewer import PageView
from .widgets import AnimatedButton, Card, DropZone, IconButton, SignaturePad, ToggleSwitch, Toast, fade_in, shake

IDLE_LOCK_MS = 5 * 60 * 1000


class _Signals(QObject):
    done = Signal(bytes)
    failed = Signal(str)


class _SignJob(QRunnable):
    def __init__(self, fn):
        super().__init__()
        self.fn, self.sig = fn, _Signals()

    def run(self):
        try:
            self.sig.done.emit(self.fn())
        except AppError as exc:
            self.sig.failed.emit(tr(exc.key, **exc.kw))
        except Exception:  # noqa: BLE001
            self.sig.failed.emit(tr("err_unexpected"))


class ViewerPane(QWidget):
    """Visor + barra flotante (páginas y zoom)."""

    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self.view = PageView()
        lay.addWidget(self.view)
        self.pill = QFrame(self)
        self.pill.setObjectName("pill")
        pl = QHBoxLayout(self.pill)
        pl.setContentsMargins(10, 6, 10, 6)
        pl.setSpacing(2)
        self.prev, self.next = IconButton("left", "", 32), IconButton("right", "", 32)
        self.zo, self.zi, self.fit = IconButton("zoom-out", "", 32), IconButton("zoom-in", "", 32), IconButton("fit", "", 32)
        self.pg = QLabel("1 / 1"); self.pg.setMinimumWidth(56); self.pg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.zl = QLabel("100%"); self.zl.setMinimumWidth(46); self.zl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        for w in (self.prev, self.pg, self.next):
            pl.addWidget(w)
        sep = QFrame(); sep.setFixedSize(1, 18); sep.setStyleSheet(f"background:{P['border']}")
        pl.addWidget(sep)
        for w in (self.zo, self.zl, self.zi, self.fit):
            pl.addWidget(w)
        self.prev.clicked.connect(lambda: self.view.goto_page(self.view.current_page() - 1))
        self.next.clicked.connect(lambda: self.view.goto_page(self.view.current_page() + 1))
        self.zo.clicked.connect(lambda: self.view.set_zoom(self.view.zoom / 1.2))
        self.zi.clicked.connect(lambda: self.view.set_zoom(self.view.zoom * 1.2))
        self.fit.clicked.connect(lambda: self.view.fit_width())
        self.view.page_changed.connect(lambda i, n: self.pg.setText(f"{i + 1} / {n}"))
        self.view.zoom_changed.connect(lambda z: self.zl.setText(f"{round(z * 100)}%"))
        self.restyle()
        self.retranslate()

    def retranslate(self):
        for b, k in ((self.prev, "tip_prev"), (self.next, "tip_next"), (self.zo, "tip_zoom_out"),
                     (self.zi, "tip_zoom_in"), (self.fit, "tip_fit")):
            b.setToolTip(tr(k))

    def restyle(self):
        self.pill.setStyleSheet(f"#pill {{ background:{P['surface']}; border:1px solid {P['border']}; border-radius:22px; }}")

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.pill.adjustSize()
        self.pill.move((self.width() - self.pill.width()) // 2, self.height() - self.pill.height() - 18)


class MainWindow(QMainWindow):
    def __init__(self, settings: Settings, audit: AuditLog, info: dict | None = None):
        super().__init__()
        self.settings, self.audit = settings, audit
        self.info = info or {"integrity": "dev", "build": "dev"}
        self.resize(1320, 840)
        self.setMinimumSize(1060, 680)
        self.setAcceptDrops(True)

        self.doc: PdfDoc | None = None
        self.pdf_path = ""
        self.signer = None
        self.cert = None
        self.limiter = AttemptLimiter()
        self.p12_data: bytes | None = None
        self.p12_name = ""
        self._sig_image = None
        self._busy = False
        self._cert_info_shown = None
        self.pool = QThreadPool.globalInstance()

        root = QWidget(); root.setObjectName("root"); self.setCentralWidget(root)
        outer = QVBoxLayout(root); outer.setContentsMargins(0, 0, 0, 0); outer.setSpacing(0)
        outer.addWidget(self._build_topbar())
        self.progress = QProgressBar(); self.progress.setRange(0, 0); self.progress.setTextVisible(False)
        self.progress.setFixedHeight(3); self.progress.hide()
        outer.addWidget(self.progress)
        body = QHBoxLayout(); body.setContentsMargins(0, 0, 0, 0); body.setSpacing(0)
        outer.addLayout(body, 1)

        self.stack = QStackedWidget()
        self.drop = DropZone(); self.drop.clicked.connect(self.open_pdf_dialog)
        self.pane = ViewerPane()
        self.stack.addWidget(self.drop); self.stack.addWidget(self.pane)
        body.addWidget(self.stack, 1)
        body.addWidget(self._build_side())

        self.toast = Toast(root)
        self.pane.view.stamp_changed.connect(self._refresh)
        self.pane.view.render_failed.connect(self._render_failed)
        self.pad.changed.connect(self._refresh)

        self.idle = QTimer(self, singleShot=True, interval=IDLE_LOCK_MS)

        self.idle.timeout.connect(self._idle_lock)
        QApplication.instance().installEventFilter(self)
        self.retranslate()
        self._refresh()
        self.audit.log("app_start")
        QTimer.singleShot(50, lambda: fade_in(self.stack.currentWidget(), 500))

    # ------------------------------------------------------------------ construcción
    def _build_topbar(self) -> QWidget:
        bar = QFrame(); bar.setObjectName("topbar"); bar.setFixedHeight(60)
        h = QHBoxLayout(bar); h.setContentsMargins(20, 0, 16, 0); h.setSpacing(8)
        self.logo_icon = QLabel(); self.logo_icon.setPixmap(theme.pixmap("stamp", P["accent"], 26))
        logo = QLabel(APP_NAME); logo.setObjectName("logo")
        self.chip = QLabel(); self.chip.setObjectName("chip"); self.chip.setFixedHeight(30)
        self.chip.setTextFormat(Qt.TextFormat.PlainText)  # el nombre de fichero no es de confianza
        h.addWidget(self.logo_icon); h.addWidget(logo); h.addSpacing(16); h.addWidget(self.chip); h.addStretch()
        self.btn_verify = IconButton("eye", "", 38); self.btn_verify.clicked.connect(self._show_sigs)
        self.btn_lang = IconButton("globe", "", 38); self.btn_lang.clicked.connect(self._lang_menu)
        self.btn_priv = IconButton("shield", "", 38); self.btn_priv.clicked.connect(self._privacy)
        self.btn_theme = IconButton("sun", "", 38); self.btn_theme.clicked.connect(self._toggle_theme)
        self.btn_about = IconButton("info", "", 38); self.btn_about.clicked.connect(self._about)
        self.btn_open = AnimatedButton("", "ghost", "file"); self.btn_open.clicked.connect(self.open_pdf_dialog)
        self.btn_close = IconButton("x", "", 38); self.btn_close.clicked.connect(self.close_doc); self.btn_close.hide()
        for w in (self.btn_verify, self.btn_lang, self.btn_priv, self.btn_theme, self.btn_about, self.btn_open, self.btn_close):
            h.addWidget(w)
        return bar

    def _build_side(self) -> QWidget:
        side = QFrame(); side.setObjectName("side"); side.setFixedWidth(372)
        sl = QVBoxLayout(side); sl.setContentsMargins(0, 0, 0, 0)
        sc = QScrollArea(); sc.setWidgetResizable(True); sc.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        inner = QWidget(); il = QVBoxLayout(inner); il.setContentsMargins(16, 16, 16, 16); il.setSpacing(14)
        sc.setWidget(inner); sl.addWidget(sc)

        # 1 · certificado
        self.c1 = Card(1, "")
        self.cert_stack = QStackedWidget()
        lock = QWidget(); ll = QVBoxLayout(lock); ll.setContentsMargins(0, 0, 0, 0); ll.setSpacing(8)
        self.p12_label = QLabel(); self.p12_label.setObjectName("muted"); self.p12_label.setWordWrap(True)
        self.p12_label.setTextFormat(Qt.TextFormat.PlainText)
        self.pick_btn = AnimatedButton("", "ghost", "key"); self.pick_btn.clicked.connect(self._pick_p12)
        self.pw = QLineEdit(); self.pw.setEchoMode(QLineEdit.EchoMode.Password)
        self.pw.setInputMethodHints(Qt.InputMethodHint.ImhHiddenText | Qt.InputMethodHint.ImhSensitiveData
                                    | Qt.InputMethodHint.ImhNoPredictiveText | Qt.InputMethodHint.ImhNoAutoUppercase)
        self.pw.returnPressed.connect(self._unlock)
        self.unlock_btn = AnimatedButton("", "primary", "lock"); self.unlock_btn.clicked.connect(self._unlock)
        for w in (self.p12_label, self.pick_btn, self.pw, self.unlock_btn):
            ll.addWidget(w)
        unlocked = QWidget(); ul = QVBoxLayout(unlocked); ul.setContentsMargins(0, 0, 0, 0); ul.setSpacing(6)
        self.cert_name = QLabel(); self.cert_name.setStyleSheet("font-weight:700; font-size:14px"); self.cert_name.setWordWrap(True)
        self.cert_name.setTextFormat(Qt.TextFormat.PlainText)
        self.cert_meta = QLabel(); self.cert_meta.setObjectName("muted"); self.cert_meta.setWordWrap(True)
        self.cert_meta.setTextFormat(Qt.TextFormat.RichText)
        self.relock_btn = AnimatedButton("", "ghost", "lock"); self.relock_btn.clicked.connect(lambda: self._lock_cert("manual"))
        for w in (self.cert_name, self.cert_meta, self.relock_btn):
            ul.addWidget(w)
        self.cert_stack.addWidget(lock); self.cert_stack.addWidget(unlocked)
        self.c1.body.addWidget(self.cert_stack)

        # 2 · bloque de firma (+ firma manuscrita opcional)
        self.c2 = Card(2, "")
        self.desc = QLabel(); self.desc.setObjectName("muted"); self.desc.setWordWrap(True)
        self.c2.body.addWidget(self.desc)
        self.sw = ToggleSwitch(); self.sw.setChecked(False)  # firma manuscrita DESACTIVADA por defecto
        self.sw.toggled.connect(self._hand_toggled)
        self.c2.body.addWidget(self.sw)
        self.pad_box = QWidget()
        pl = QVBoxLayout(self.pad_box); pl.setContentsMargins(0, 4, 0, 0); pl.setSpacing(8)
        self.pad = SignaturePad(); pl.addWidget(self.pad)
        row = QHBoxLayout(); row.setSpacing(6)
        self.ink_btns = []
        for col in SignaturePad.INKS:
            b = QFrame(); b.setFixedSize(22, 22); b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.mousePressEvent = lambda _e, c=col: self._set_ink(c)
            self.ink_btns.append((b, col)); row.addWidget(b)
        row.addStretch()
        self.undo = IconButton("undo", "", 34); self.undo.clicked.connect(self.pad.undo)
        self.clear = IconButton("trash", "", 34); self.clear.clicked.connect(self.pad.clear)
        row.addWidget(self.undo); row.addWidget(self.clear)
        pl.addLayout(row)
        self.pad_box.setMaximumHeight(0)
        self.pad_anim = QPropertyAnimation(self.pad_box, b"maximumHeight", self)
        self.pad_anim.setDuration(320); self.pad_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.c2.body.addWidget(self.pad_box)
        self.place_btn = AnimatedButton("", "primary", "pen"); self.place_btn.clicked.connect(self._place)
        self.c2.body.addWidget(self.place_btn)
        self._set_ink(SignaturePad.INKS[0])

        # 3 · firmar
        self.c3 = Card(3, "")
        self.reason = QLineEdit(); self.reason.setMaxLength(120)
        self.sign_btn = AnimatedButton("", "primary", "stamp"); self.sign_btn.setMinimumHeight(48)
        self.sign_btn.clicked.connect(self._sign)
        self.status = QLabel(); self.status.setObjectName("muted"); self.status.setWordWrap(True)
        for w in (self.reason, self.sign_btn, self.status):
            self.c3.body.addWidget(w)

        for c in (self.c1, self.c2, self.c3):
            il.addWidget(c)
        il.addStretch()
        return side

    # ------------------------------------------------------------------ idioma
    def retranslate(self):
        self.setWindowTitle(APP_NAME)
        self.btn_verify.setToolTip(tr("tip_sigs")); self.btn_lang.setToolTip(tr("tip_lang"))
        self.btn_priv.setToolTip(tr("tip_privacy")); self.btn_theme.setToolTip(tr("tip_theme"))
        self.btn_about.setToolTip(tr("tip_about")); self.btn_open.setText(tr("btn_open"))
        self.btn_close.setToolTip(tr("tip_close_doc"))
        self._update_chip()
        self.c1.title.setText(tr("c1_title")); self.c2.title.setText(tr("c2_title")); self.c3.title.setText(tr("c3_title"))
        self.p12_label.setText(f"🔑 {self.p12_name}" if self.p12_name and self.p12_data else tr("c1_none"))
        self.pick_btn.setText(tr("c1_pick")); self.pw.setPlaceholderText(tr("c1_pw"))
        self.unlock_btn.setText(tr("c1_unlock")); self.relock_btn.setText(tr("c1_lock"))
        if self.cert:
            self._show_cert()
        self.desc.setText(tr("c2_desc")); self.sw.setText(tr("sw_hand"))
        self.undo.setToolTip(tr("tip_undo")); self.clear.setToolTip(tr("tip_clear"))
        self.reason.setPlaceholderText(tr("reason_ph"))
        self.sign_btn.setText(tr("signing") if self._busy else tr("btn_sign"))
        self.pane.retranslate()
        self.drop.update(); self.pad.update()
        self._refresh()

    def _lang_menu(self):
        menu = QMenu(self)
        for code, name in LANGUAGES:
            act = menu.addAction(("● " if code == self.settings.language else "    ") + name)
            act.triggered.connect(lambda _c=False, c=code: self._set_lang(c))
        menu.exec(self.btn_lang.mapToGlobal(self.btn_lang.rect().bottomLeft()))

    def _set_lang(self, code: str):
        self.settings.language = set_language(code)
        save_settings(self.settings)
        self.retranslate()

    def _update_chip(self):
        if self.doc:
            n = self.doc.page_count
            self.chip.setText(f"{os.path.basename(self.pdf_path)} · {tr('pages_one') if n == 1 else tr('pages_many', n=n)}")
        else:
            self.chip.setText(tr("no_doc"))

    # ------------------------------------------------------------------ estado
    def _set_ink(self, col: str):
        self.pad.set_ink(col)
        for b, c in self.ink_btns:
            b.setStyleSheet(f"background:{c}; border-radius:11px; border:{'3px solid ' + P['accent'] if c == col else '2px solid ' + P['border']};")

    def _hand_toggled(self, on: bool):
        self.pad_anim.stop()
        self.pad_anim.setStartValue(self.pad_box.maximumHeight())
        if on:
            self.pad_box.setMaximumHeight(0)
            self.pad_anim.setEndValue(self.pad_box.sizeHint().height() + 8)
            self.pad_anim.finished.connect(lambda: self.pad_box.setMaximumHeight(16777215) if self.sw.isChecked() else None,
                                           Qt.ConnectionType.SingleShotConnection)
        else:
            self.pad_anim.setEndValue(0)
        self.pad_anim.start()
        self._sync_stamp()
        self._refresh()

    def _lines(self) -> list[str]:
        name = self.cert.common_name if self.cert else tr("stamp_placeholder")
        return [tr("stamp_signed_by"), name, f"{datetime.now().astimezone():%Y-%m-%d %H:%M %z}"]

    def _use_image(self) -> bool:
        return self.sw.isChecked() and self.pad.has_ink()

    def _sync_stamp(self):
        """Mantiene el bloque ya colocado coherente con el interruptor / la firma dibujada."""
        v = self.pane.view
        if v.has_stamp():
            img = self.pad.to_image() if self._use_image() else None
            self._sig_image = img
            v.stamp.set_content(img, self._lines())
            v.stamp_changed.emit()

    def _refresh(self, *_):
        has_doc = self.doc is not None
        has_stamp = self.pane.view.has_stamp()
        need_ink = self.sw.isChecked() and not self.pad.has_ink()
        self.c1.set_done(self.signer is not None)
        self.c2.set_done(has_stamp)
        ink = self.pad.has_ink()
        self.undo.setEnabled(ink); self.clear.setEnabled(ink)
        self.place_btn.setEnabled(has_doc and not need_ink)
        self.place_btn.setText(tr("btn_replace") if has_stamp else tr("btn_place"))
        if has_stamp:
            self.pane.view.stamp.set_lines(self._lines())
        ready = has_doc and self.signer is not None and has_stamp and not self._busy and not need_ink
        self.sign_btn.setEnabled(ready)
        missing = []
        if not has_doc: missing.append(tr("miss_pdf"))
        if self.signer is None: missing.append(tr("miss_cert"))
        if need_ink: missing.append(tr("miss_ink"))
        elif has_doc and not has_stamp: missing.append(tr("miss_stamp"))
        self.status.setText(tr("status_missing", items=", ".join(missing)) if missing else tr("status_ready"))
        self.c3.set_done(False)

    def _toggle_theme(self):
        dark = not theme.IS_DARK
        self.settings.theme = "dark" if dark else "light"
        save_settings(self.settings)
        self.apply_theme(dark)

    def apply_theme(self, dark: bool):
        theme.set_theme(dark)
        QApplication.instance().setStyleSheet(theme.stylesheet())
        self.btn_theme.set_name("sun" if dark else "moon")
        self.logo_icon.setPixmap(theme.pixmap("stamp", P["accent"], 26))
        self.pane.restyle()
        self._set_ink(self.pad.ink)
        self.update()

    # ------------------------------------------------------------------ documento
    def open_pdf_dialog(self):
        path, _ = QFileDialog.getOpenFileName(self, tr("dlg_open_pdf"), "", tr("filter_pdf"))
        if path:
            self.open_pdf(path)

    def open_pdf(self, path: str):
        try:
            data = read_regular_file(path, MAX_PDF_BYTES, b"%PDF-")
            doc = PdfDoc(data)
        except InputRejected as exc:
            self.toast.show_message(tr(exc.key, **exc.kw), "error")
            return
        self._load_doc(doc, path)
        self.audit.log("doc_open", doc=doc_fingerprint(data), pages=doc.page_count)

    def _load_doc(self, doc: PdfDoc, path: str):
        if self.doc:
            self.doc.close()
        self.doc, self.pdf_path = doc, path
        self.pane.view.load(doc)
        self._update_chip()
        if not self.btn_close.isVisible():
            self.btn_close.show(); fade_in(self.btn_close, 250)
        if self.stack.currentWidget() is not self.pane:
            self.stack.setCurrentWidget(self.pane)
        fade_in(self.pane, 350)
        QTimer.singleShot(0, lambda: self.pane.view.fit_width(animated=False))
        self._refresh()
        n = len(check_signatures(doc.data))
        if n:
            self.toast.show_message(tr("toast_existing", n=n), "info")

    def _render_failed(self, key: str):
        self.toast.show_message(tr(key), "error")
        QTimer.singleShot(0, self.close_doc)

    def close_doc(self):
        """Descarta el documento actual y vuelve a la pantalla de inicio."""
        if self._busy or not self.doc:
            return
        self.pane.view.clear()
        self.doc.close()
        self.doc, self.pdf_path, self._sig_image = None, "", None
        self.btn_close.hide(); self.toast.hide()
        self.stack.setCurrentWidget(self.drop)
        fade_in(self.drop, 350)
        self._update_chip()
        self._refresh()

    def _show_sigs(self):
        if not self.doc:
            self.toast.show_message(tr("toast_open_first"), "warn"); return
        self.audit.log("verify")
        VerifyDialog(check_signatures(self.doc.data), self).exec()

    # ------------------------------------------------------------------ certificado
    def _pick_p12(self):
        path, _ = QFileDialog.getOpenFileName(self, tr("dlg_pick_p12"), "", tr("filter_p12"))
        if not path:
            return
        try:
            self.p12_data = read_regular_file(path, MAX_P12_BYTES)
        except InputRejected as exc:
            self.toast.show_message(tr(exc.key, **exc.kw), "error"); return
        self.p12_name = os.path.basename(path)
        self.p12_label.setText(f"🔑 {self.p12_name}")
        self.pw.setFocus()

    def _unlock(self):
        if not self.p12_data:
            self.toast.show_message(tr("toast_pick_p12"), "warn"); return
        wait = self.limiter.remaining()
        if wait > 0:
            self.toast.show_message(tr("toast_wait", s=int(wait) + 1), "warn"); return
        secret = Secret(self.pw.text())
        try:
            self.signer, self.cert = load_pkcs12(self.p12_data, secret)
        except CertificateError as exc:
            self.limiter.failure()
            self.audit.log("cert_load_fail")
            shake(self.pw); self.toast.show_message(tr(exc.key, **exc.kw), "error"); return
        finally:
            secret.wipe(); self.pw.clear()
        self.limiter.success()
        self.p12_data = None  # el fichero ya no se retiene
        self.audit.log("cert_load_ok")
        self._show_cert()
        self.cert_stack.setCurrentIndex(1); fade_in(self.cert_stack.currentWidget(), 300)
        self.toast.show_message(tr("toast_expired") if self.cert.expired else tr("toast_unlocked"),
                                "warn" if self.cert.expired else "ok")
        self.idle.start()
        self._sync_stamp()
        self._refresh()

    def _show_cert(self):
        c = self.cert
        col = P["danger"] if c.expired else P["muted"]
        validity = tr("c1_expired", date=f"{c.not_after:%Y-%m-%d}") if c.expired else tr("c1_valid", date=f"{c.not_after:%Y-%m-%d}")
        issuer = c.issuer.replace("<", "&lt;").replace(">", "&gt;")
        self.cert_name.setText(f"✔ {c.common_name}")
        self.cert_meta.setText(f"{tr('c1_issuer', issuer=issuer)}<br><span style='color:{col}'>{validity}</span>")

    def _lock_cert(self, reason: str):
        self.signer = self.cert = None
        self.p12_data = None
        self.p12_name = ""
        self.p12_label.setText(tr("c1_none"))
        self.pw.clear()
        self.cert_stack.setCurrentIndex(0); fade_in(self.cert_stack.currentWidget(), 300)
        self.audit.log("cert_lock", reason=reason)
        self._sync_stamp()
        self._refresh()

    def _idle_lock(self):
        if self.signer is not None:
            self._lock_cert("idle")
            self.pad.wipe()
            self.toast.show_message(tr("toast_idle"), "warn")

    def eventFilter(self, obj, ev):
        if ev.type() in (QEvent.Type.MouseButtonPress, QEvent.Type.KeyPress) and self.signer is not None:
            self.idle.start()
        return super().eventFilter(obj, ev)

    # ------------------------------------------------------------------ firma
    def _place(self):
        if not self.doc:
            return
        self._sig_image = self.pad.to_image() if self._use_image() else None
        self.pane.view.place_stamp(self._sig_image, self._lines())

    def _sign(self):
        if self._busy or not (self.doc and self.signer and self.pane.view.has_stamp()):
            return
        placement = self.pane.view.stamp_placement()
        if not placement:
            self.toast.show_message(tr("toast_place_page"), "warn"); return
        page, r = placement
        box = self.doc.to_pdf_box(page, r.left(), r.top(), r.right(), r.bottom())
        default = os.path.splitext(os.path.basename(self.pdf_path))[0] + "_signed.pdf"
        out_path, _ = QFileDialog.getSaveFileName(self, tr("dlg_save"), os.path.join(os.path.dirname(self.pdf_path), default), "PDF (*.pdf)")
        if not out_path:
            return
        if not out_path.lower().endswith(".pdf"):
            out_path += ".pdf"
        if os.path.realpath(out_path) == os.path.realpath(self.pdf_path):
            self.toast.show_message(tr("toast_overwrite"), "error"); return
        png = None
        if self._sig_image is not None:
            ba = QByteArray(); buf = QBuffer(ba); buf.open(QIODevice.OpenModeFlag.WriteOnly)
            self._sig_image.save(buf, "PNG"); png = bytes(ba)
        data, signer, reason, lines = self.doc.data, self.signer, self.reason.text().strip(), self._lines()
        self._busy = True; self.progress.show(); self._refresh()
        self.sign_btn.setText(tr("signing"))
        job = _SignJob(lambda: sign_pdf(data, signer, page, box, lines, png, reason))
        job.sig.done.connect(lambda out: self._signed(out, out_path, data))
        job.sig.failed.connect(self._sign_failed)
        self.pool.start(job)
        self._job = job  # mantener las señales vivas

    def _end_busy(self):
        self._busy = False; self.progress.hide(); self.sign_btn.setText(tr("btn_sign"))

    def _signed(self, out: bytes, out_path: str, original: bytes):
        try:
            atomic_write(out_path, out, 0o600)
        except OSError:
            self._end_busy(); self.audit.log("sign_fail", code="write")
            self.toast.show_message(tr("toast_save_fail"), "error"); self._refresh(); return
        self._end_busy()
        self.audit.log("sign_ok", doc=doc_fingerprint(original), out=doc_fingerprint(out))
        self.pane.view.remove_stamp()
        self.pad.wipe(); self.pad.clear()
        self._sig_image = None
        self._load_doc(PdfDoc(out), out_path)
        self.toast.show_message(tr("toast_signed", name=os.path.basename(out_path)), "ok", 5200)

    def _sign_failed(self, msg: str):
        self._end_busy(); self.audit.log("sign_fail", code="sign")
        self.toast.show_message(msg, "error"); self._refresh()

    # ------------------------------------------------------------------ varios
    def _privacy(self):
        dlg = PrivacyDialog(self.settings, self.audit, self)
        dlg.exec()
        if dlg.erased:
            QApplication.instance().quit()

    def _about(self):
        AboutDialog(self.info["integrity"], self.info["build"], self).exec()

    def dragEnterEvent(self, e):
        urls = e.mimeData().urls()
        if len(urls) == 1 and urls[0].isLocalFile() and urls[0].toLocalFile().lower().endswith(".pdf"):
            e.acceptProposedAction(); self.drop.set_drag(True)

    def dragLeaveEvent(self, e):
        self.drop.set_drag(False)

    def dropEvent(self, e):
        self.drop.set_drag(False)
        self.open_pdf(e.mimeData().urls()[0].toLocalFile())

    def closeEvent(self, e):
        self.pad.wipe()
        self.signer = None
        super().closeEvent(e)
