#!/usr/bin/env python3
"""Genera las capturas de docs/assets con la propia interfaz (modo offscreen) y un certificado de demostración."""
import math
import os
import sys
import tempfile
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
tmp = tempfile.mkdtemp()
os.environ["XDG_CONFIG_HOME"] = os.environ["XDG_STATE_HOME"] = tmp
sys.path[:0] = [ROOT, os.path.join(ROOT, "tests")]

import pymupdf
from PIL import Image
from PySide6.QtCore import QEvent, QPointF, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QApplication

import test_core as T
from tuxsign import i18n
from tuxsign.audit import AuditLog
from tuxsign.privacy import Settings
from tuxsign.ui import theme
from tuxsign.ui.main_window import MainWindow

OUT = os.path.join(ROOT, "docs", "assets")
DOCS = {
    "en": ("Service agreement", [
        "This agreement is made between the Client and the Provider on the date shown below.",
        "1. Scope. The Provider will deliver the design and development work described in Annex A.",
        "2. Fees. The Client will pay the agreed fee within thirty days of each invoice.",
        "3. Confidentiality. Both parties keep the contents of this agreement and of the project private.",
        "4. Term. The agreement stays in force for twelve months and renews unless either party objects.",
    ], "Signed for the Provider:"),
    "es": ("Contrato de prestación de servicios", [
        "Este contrato se celebra entre el Cliente y el Proveedor en la fecha que figura abajo.",
        "1. Objeto. El Proveedor entregará el trabajo de diseño y desarrollo descrito en el Anexo A.",
        "2. Honorarios. El Cliente pagará la cantidad acordada en los treinta días siguientes a cada factura.",
        "3. Confidencialidad. Ambas partes mantendrán en privado el contenido de este contrato y del proyecto.",
        "4. Duración. El contrato dura doce meses y se renueva si ninguna de las partes se opone.",
    ], "Firma del Proveedor:"),
}


FILENAMES = {"en": "service-agreement.pdf", "es": "contrato-servicios.pdf"}


def make_pdf(lang: str) -> bytes:
    title, clauses, sign_line = DOCS[lang]
    d = pymupdf.open()
    p = d.new_page(width=595, height=842)
    p.insert_text((64, 96), title, fontsize=22, fontname="hebo")
    y = 150
    for c in clauses:
        rect = pymupdf.Rect(64, y, 531, y + 60)
        p.insert_textbox(rect, c, fontsize=11.5, fontname="helv", lineheight=1.5)
        y += 62
    p.insert_text((64, 640), sign_line, fontsize=11, fontname="helv")
    return d.tobytes()


app = QApplication([])


def pump(n=12):
    for _ in range(n):
        app.processEvents()
    time.sleep(0.45)
    for _ in range(n):
        app.processEvents()


def ev(t, x, y):
    return QMouseEvent(t, QPointF(x, y), QPointF(x, y), Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)


def scribble(pad):
    """Una firma con aire de firma: trazo largo con bucles y una rúbrica aparte."""
    pad.mousePressEvent(ev(QEvent.MouseButtonPress, 30, 100))
    for i in range(120):
        t = i / 119
        x = 30 + 215 * t
        y = 98 - 50 * math.sin(t * 11) * math.exp(-t * 1.6) - 10 * t
        pad.mouseMoveEvent(ev(QEvent.MouseMove, x, y))
        time.sleep(0.002)
    pad.mouseReleaseEvent(ev(QEvent.MouseButtonRelease, 245, 88))
    pad.mousePressEvent(ev(QEvent.MouseButtonPress, 70, 122))
    for i in range(40):
        t = i / 39
        pad.mouseMoveEvent(ev(QEvent.MouseMove, 70 + 175 * t, 122 - 6 * t + 2 * math.sin(t * 7)))
        time.sleep(0.002)
    pad.mouseReleaseEvent(ev(QEvent.MouseButtonRelease, 245, 116))


for lang in ("en", "es"):
    i18n.set_language(lang)
    for dark in (True, False):
        theme.set_theme(dark)
        app.setStyleSheet(theme.stylesheet())
        s = Settings(); s.language = lang
        w = MainWindow(s, AuditLog(False))
        w.apply_theme(dark); w.resize(1320, 840); w.show(); pump()
        tag = f"{lang}-{'dark' if dark else 'light'}"
        w.grab().save(f"{OUT}/home-{tag}.png")
        pdf = os.path.join(tmp, FILENAMES[lang]); open(pdf, "wb").write(make_pdf(lang))
        w.open_pdf(pdf); pump()
        w.p12_data = T.make_p12(cn="Ana García (demo)"); w.pw.setText("pw"); w._unlock(); pump(); w.toast.hide()
        v = w.pane.view
        v.set_zoom(0.86, animated=False); pump()
        w._place(); pump()
        v.stamp.setPos(v.stamp.pos().x(), v.stamp.scene().sceneRect().top() + 40 + 666); v.centerOn(v.stamp); pump()
        w.toast.hide(); pump(); w.grab().save(f"{OUT}/block-{tag}.png")
        w.sw.setChecked(True); pump(30)
        scribble(w.pad); w._place(); pump(); w.toast.hide(); pump()
        w.grab().save(f"{OUT}/handwritten-{tag}.png")
        w.close()

# optimizar
for f in sorted(os.listdir(OUT)):
    if f.endswith(".png"):
        im = Image.open(os.path.join(OUT, f)).convert("RGB")
        im.save(os.path.join(OUT, f.replace(".png", ".webp")), "WEBP", quality=88, method=6)
        os.unlink(os.path.join(OUT, f))
print("capturas:", sorted(os.listdir(OUT)))
