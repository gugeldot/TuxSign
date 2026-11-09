"""Prueba de humo de la UI (offscreen por defecto, o QT_QPA_PLATFORM=wayland para pantalla real) con capturas."""
import math, os, sys, tempfile, time
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
tmp = tempfile.mkdtemp()
os.environ["XDG_CONFIG_HOME"] = os.environ["XDG_STATE_HOME"] = tmp
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))
if os.environ.get("TUXSIGN_NATIVE_LIB"):  # probar contra el build nativo (.so) en vez del código fuente
    sys.path.insert(0, os.environ["TUXSIGN_NATIVE_LIB"])
from PySide6.QtCore import QEvent, QPointF, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QApplication
from tuxsign import i18n
from tuxsign.audit import AuditLog
from tuxsign.pdfdoc import PdfDoc
from tuxsign.privacy import Settings
from tuxsign.signer import check_signatures, sign_pdf
from tuxsign.ui import theme
from tuxsign.ui.main_window import MainWindow
import test_core as T

OUT = sys.argv[1] if len(sys.argv) > 1 else tmp
app = QApplication([])
theme.set_theme(True); app.setStyleSheet(theme.stylesheet())
w = MainWindow(Settings(), AuditLog()); w.apply_theme(True); w.show()
def pump(n=15):
    for _ in range(n): app.processEvents()
    time.sleep(0.5)
    for _ in range(n): app.processEvents()
def shot(name): w.grab().save(f"{OUT}/{name}.png")

assert i18n.current() == "en" and not w.sw.isChecked(), "default: English, handwriting OFF"
pump(); shot("1_welcome")
pdf = os.path.join(tmp, "doc.pdf"); open(pdf, "wb").write(T.make_pdf())
w.open_pdf(pdf); pump()
w.p12_data = T.make_p12(); w.pw.setText("pw"); w._unlock(); pump()
assert w.signer is not None
w._place(); pump()                               # bloque solo-texto (sin firma manuscrita)
v = w.pane.view; assert v.has_stamp() and v.stamp.pix is None
v.stamp.setPos(v.stamp.pos().x() + 100, v.stamp.pos().y() + 220); pump(); shot("2_text_block")

# interruptor → firma manuscrita
w.sw.setChecked(True); pump(30)
assert not w.place_btn.isEnabled()               # sin trazo no se puede colocar
def ev(t, x, y): return QMouseEvent(t, QPointF(x, y), QPointF(x, y), Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
pad = w.pad
pad.mousePressEvent(ev(QEvent.MouseButtonPress, 30, 100))
for i in range(60):
    pad.mouseMoveEvent(ev(QEvent.MouseMove, 30 + i * 3.6, 90 + 40 * math.sin(i / 5) * (1 - i / 80))); time.sleep(0.004)
pad.mouseReleaseEvent(ev(QEvent.MouseButtonRelease, 200, 100))
w._place(); pump(); assert v.stamp.pix is not None; shot("3_with_handwriting")

# firmar (flujo interno, sin diálogos de fichero)
page, r = v.stamp_placement(); box = w.doc.to_pdf_box(page, r.left(), r.top(), r.right(), r.bottom())
from PySide6.QtCore import QBuffer, QByteArray, QIODevice
ba = QByteArray(); b = QBuffer(ba); b.open(QIODevice.WriteOnly); w._sig_image.save(b, "PNG")
out = sign_pdf(w.doc.data, w.signer, page, box, w._lines(), bytes(ba))
assert check_signatures(out)[0].intact
v.remove_stamp(); w._load_doc(PdfDoc(out), pdf); pump(); shot("4_signed")

# cerrar documento → vuelve a la pantalla de inicio
assert w.btn_close.isVisible()
w.close_doc(); pump(); assert w.doc is None and w.stack.currentWidget() is w.drop and not w.btn_close.isVisible(); shot("4b_closed")
w.open_pdf(pdf); pump(); assert w.btn_close.isVisible()
# idioma + tema claro
w._set_lang("es"); pump(); assert i18n.tr("btn_open") == "Abrir PDF"; shot("5_es")
theme.set_theme(False); w.apply_theme(False); w._set_lang("de"); pump(); shot("6_de_light")
print("SMOKE OK", AuditLog().verify(), "platform:", app.platformName())
