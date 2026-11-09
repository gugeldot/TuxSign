"""Widgets propios con animaciones: botón, tarjeta, toast, drop-zone y pad de firma."""
from __future__ import annotations

from PySide6.QtCore import (
    QEasingCurve, QPoint, QPointF, QPropertyAnimation, QRectF, QSequentialAnimationGroup, QSize, Qt, QTimer,
    QVariantAnimation, Signal,
)
from PySide6.QtGui import QBrush, QColor, QImage, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QFrame, QGraphicsOpacityEffect, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget,
)

from ..i18n import tr
from . import theme
from .theme import P, icon, mix


def fade_in(widget: QWidget, ms: int = 280, delay: int = 0) -> QPropertyAnimation:
    eff = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(eff)
    anim = QPropertyAnimation(eff, b"opacity", widget)
    anim.setDuration(ms)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.Type.OutCubic)
    anim.finished.connect(lambda: widget.setGraphicsEffect(None))
    QTimer.singleShot(delay, anim.start)
    return anim


def shake(widget: QWidget) -> None:
    """Animación de error (contraseña incorrecta)."""
    base = widget.pos()
    seq = QSequentialAnimationGroup(widget)
    for dx in (-8, 8, -5, 5, -2, 0):
        a = QPropertyAnimation(widget, b"pos", widget)
        a.setDuration(45)
        a.setEndValue(base + QPoint(dx, 0))
        seq.addAnimation(a)
    seq.start(QSequentialAnimationGroup.DeletionPolicy.DeleteWhenStopped)


class AnimatedButton(QPushButton):
    """Botón con transición suave de hover/press. kind: primary | ghost | danger."""

    def __init__(self, text: str = "", kind: str = "primary", icon_name: str | None = None, parent=None):
        super().__init__(text, parent)
        self.kind = kind
        self.icon_name = icon_name
        self._h = 0.0
        self._press = 0.0
        self._anim = QVariantAnimation(self, duration=160)
        self._anim.valueChanged.connect(self._set_h)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(40)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def _set_h(self, v):
        self._h = float(v)
        self.update()

    def _go(self, target: float):
        self._anim.stop()
        self._anim.setStartValue(self._h)
        self._anim.setEndValue(target)
        self._anim.start()

    def enterEvent(self, e):
        self._go(1.0)
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._go(0.0)
        super().leaveEvent(e)

    def mousePressEvent(self, e):
        self._press = 1.0
        self.update()
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        self._press = 0.0
        self.update()
        super().mouseReleaseEvent(e)

    def sizeHint(self):
        fm = self.fontMetrics()
        return QSize(fm.horizontalAdvance(self.text()) + (56 if self.icon_name else 36), 40)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        if self._press:
            r = r.adjusted(1, 1, -1, -1)
        on = self.isEnabled()
        if self.kind == "primary":
            a, b = QColor(P["accent"]), QColor(P["accent2"])
            b = mix(P["accent"], P["accent2"], 0.35 + 0.65 * self._h)
            from PySide6.QtGui import QLinearGradient
            g = QLinearGradient(r.topLeft(), r.bottomRight())
            g.setColorAt(0, a)
            g.setColorAt(1, b)
            p.setBrush(QBrush(g))
            p.setPen(Qt.PenStyle.NoPen)
            fg = P["on_accent"]
        elif self.kind == "danger":
            p.setBrush(mix(P["surface2"], P["danger"], 0.18 + 0.25 * self._h))
            p.setPen(QPen(mix(P["border"], P["danger"], 0.6), 1))
            fg = P["danger"]
        else:
            p.setBrush(mix(P["surface2"], P["accent"], 0.12 * self._h))
            p.setPen(QPen(mix(P["border"], P["accent"], self._h), 1))
            fg = P["text"]
        if not on:
            p.setOpacity(0.4)
        p.drawRoundedRect(r, 11, 11)
        p.setPen(QColor(fg))
        f = self.font()
        f.setWeight(f.Weight.DemiBold)
        p.setFont(f)
        fm = self.fontMetrics()
        tw = fm.horizontalAdvance(self.text())
        iw = 22 if self.icon_name else 0
        x = (self.width() - tw - iw) / 2
        if self.icon_name:
            px = theme.pixmap(self.icon_name, fg, 18)
            p.drawPixmap(int(x), int((self.height() - 18) / 2), px)
        p.drawText(QRectF(x + iw, 0, tw + 4, self.height()), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, self.text())


class IconButton(QPushButton):
    def __init__(self, name: str, tip: str = "", size: int = 36, parent=None):
        super().__init__(parent)
        self.name = name
        self.setToolTip(tip)
        self.setFixedSize(size, size)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._h = 0.0
        self._anim = QVariantAnimation(self, duration=140)
        self._anim.valueChanged.connect(self._set)
    def _set(self, v):
        self._h = float(v)
        self.update()

    def set_name(self, name: str):
        self.name = name
        self.update()

    def enterEvent(self, e):
        self._anim.stop(); self._anim.setStartValue(self._h); self._anim.setEndValue(1.0); self._anim.start()

    def leaveEvent(self, e):
        self._anim.stop(); self._anim.setStartValue(self._h); self._anim.setEndValue(0.0); self._anim.start()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(mix(P["surface"], P["surface2"], self._h) if self._h else Qt.GlobalColor.transparent)
        p.drawRoundedRect(self.rect(), 10, 10)
        if not self.isEnabled():
            p.setOpacity(0.35)
        col = P["accent"] if self._h > 0.5 else P["muted"]
        p.drawPixmap((self.width() - 18) // 2, (self.height() - 18) // 2, theme.pixmap(self.name, col, 18))


class Card(QFrame):
    """Tarjeta con número de paso (badge animado a ✓ cuando está completo) y título."""

    def __init__(self, step: int, title: str, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self._done = 0.0
        self._anim = QVariantAnimation(self, duration=350)
        self._anim.valueChanged.connect(self._set)
        self._anim.setEasingCurve(QEasingCurve.Type.OutBack)
        self.step = step
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 14, 16, 16)
        lay.setSpacing(10)
        head = QHBoxLayout()
        head.setSpacing(10)
        self._badge_paint = _Badge(self)
        self.title = QLabel(title)
        self.title.setObjectName("cardTitle")
        head.addWidget(self._badge_paint)
        head.addWidget(self.title, 1)
        lay.addLayout(head)
        self.body = QVBoxLayout()
        self.body.setSpacing(8)
        lay.addLayout(self.body)

    def _set(self, v):
        self._done = float(v)
        self._badge_paint.progress = self._done
        self._badge_paint.update()

    def set_done(self, done: bool):
        self._anim.stop()
        self._anim.setStartValue(self._done)
        self._anim.setEndValue(1.0 if done else 0.0)
        self._anim.start()


class _Badge(QWidget):
    def __init__(self, card: Card):
        super().__init__(card)
        self.card = card
        self.progress = 0.0
        self.setFixedSize(24, 24)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        t = max(0.0, min(1.0, self.progress))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(mix(P["border"], P["ok"], t))
        s = 1.0 + 0.12 * (1 - abs(2 * t - 1))
        c = self.rect().center()
        p.translate(c.x() + .5, c.y() + .5)
        p.scale(s, s)
        p.drawEllipse(QPointF(0, 0), 11, 11)
        if t > 0.5:
            p.resetTransform()
            p.drawPixmap(4, 4, theme.pixmap("check", P["on_accent"] if not theme.IS_DARK else "#06210F", 16))
        else:
            p.setPen(QColor(P["muted"]))
            f = self.font(); f.setBold(True); f.setPointSize(9); p.setFont(f)
            p.resetTransform()
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, str(self.card.step))


class Toast(QLabel):
    """Notificación flotante con deslizamiento + fundido."""

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setTextFormat(Qt.TextFormat.PlainText)  # los mensajes incluyen nombres de fichero
        self.setWordWrap(True)
        self.setMaximumWidth(420)
        self.hide()
        self._eff = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._eff)
        self._timer = QTimer(self, singleShot=True)
        self._timer.timeout.connect(self._hide)
        self._pos_anim = QPropertyAnimation(self, b"pos", self)
        self._op_anim = QPropertyAnimation(self._eff, b"opacity", self)

    def show_message(self, text: str, kind: str = "info", ms: int = 4200):
        col = {"ok": P["ok"], "error": P["danger"], "warn": P["warn"]}.get(kind, P["accent"])
        self.setStyleSheet(
            f"background:{P['surface']}; color:{P['text']}; border:1px solid {col}; border-left:4px solid {col};"
            "border-radius:12px; padding:12px 16px; font-weight:600;"
        )
        self.setText(text)
        self.adjustSize()
        par = self.parentWidget()
        x = (par.width() - self.width()) // 2
        end = QPoint(x, par.height() - self.height() - 88)
        self.move(end + QPoint(0, 30))
        self.show()
        self.raise_()
        for a, s, e in ((self._pos_anim, self.pos(), end), (self._op_anim, 0.0, 1.0)):
            a.stop(); a.setDuration(280); a.setStartValue(s); a.setEndValue(e)
            a.setEasingCurve(QEasingCurve.Type.OutCubic); a.start()
        self._timer.start(ms)

    def _hide(self):
        self._op_anim.stop(); self._op_anim.setDuration(300)
        self._op_anim.setStartValue(self._eff.opacity()); self._op_anim.setEndValue(0.0)
        self._op_anim.finished.connect(self.hide, Qt.ConnectionType.SingleShotConnection)
        self._op_anim.start()


class DropZone(QWidget):
    """Pantalla de bienvenida con borde discontinuo animado y soporte arrastrar-soltar."""

    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._phase = 0.0
        self._hover = 0.0
        self._drag = False
        self.setAcceptDrops(False)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._anim = QVariantAnimation(self, startValue=0.0, endValue=24.0, duration=1800, loopCount=-1)
        self._anim.valueChanged.connect(self._tick)
        self._anim.start()
        self._h = QVariantAnimation(self, duration=200)
        self._h.valueChanged.connect(self._sethover)
    def _tick(self, v):
        self._phase = float(v)
        self.update()

    def _sethover(self, v):
        self._hover = float(v)

    def set_drag(self, on: bool):
        self._drag = on
        self._h.stop(); self._h.setStartValue(self._hover); self._h.setEndValue(1.0 if on else 0.0); self._h.start()

    def enterEvent(self, e):
        self._h.stop(); self._h.setStartValue(self._hover); self._h.setEndValue(1.0); self._h.start()

    def leaveEvent(self, e):
        if not self._drag:
            self._h.stop(); self._h.setStartValue(self._hover); self._h.setEndValue(0.0); self._h.start()

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        bw, bh = min(560, w - 80), min(340, h - 80)
        r = QRectF((w - bw) / 2, (h - bh) / 2, bw, bh)
        p.setBrush(mix(P["viewer"], P["accent"], 0.04 + 0.08 * self._hover))
        pen = QPen(mix(P["border"], P["accent"], 0.4 + 0.6 * self._hover), 2, Qt.PenStyle.CustomDashLine)
        pen.setDashPattern([6, 6])
        pen.setDashOffset(-self._phase / 2)
        p.setPen(pen)
        p.drawRoundedRect(r, 24, 24)
        bob = 4 * (1 if (self._phase % 24) < 12 else -1) * 0  # icono estático, el borde ya anima
        px = theme.pixmap("upload", P["accent"], 56)
        p.drawPixmap(int(r.center().x() - 28), int(r.top() + 56 + bob), px)
        p.setPen(QColor(P["text"]))
        f = self.font(); f.setPointSize(17); f.setBold(True); p.setFont(f)
        p.drawText(QRectF(r.left(), r.top() + 128, r.width(), 36), Qt.AlignmentFlag.AlignCenter, tr("drop_title"))
        f.setPointSize(11); f.setBold(False); p.setFont(f)
        p.setPen(QColor(P["muted"]))
        p.drawText(QRectF(r.left(), r.top() + 168, r.width(), 24), Qt.AlignmentFlag.AlignCenter, tr("drop_sub"))
        p.drawText(QRectF(r.left(), r.top() + 230, r.width(), 24), Qt.AlignmentFlag.AlignCenter,
                   tr("drop_foot"))


class SignaturePad(QWidget):
    """Lienzo cuadrado de firma: trazo suavizado con grosor por velocidad, deshacer, tintas."""

    changed = Signal(bool)  # hay trazo
    INKS = ["#0B1020", "#1D3FBF", "#7A1230"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(280, 170)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setMouseTracking(False)
        self.strokes: list[list[tuple[float, float, float]]] = []
        self.ink = self.INKS[0]
        self._cur: list[tuple[float, float, float]] | None = None
        self._last_t = 0.0
        self._hint = 1.0
        self._hint_anim = QVariantAnimation(self, duration=300)
        self._hint_anim.valueChanged.connect(self._sethint)
        self._clock = QTimer(self)
        self._clock.setSingleShot(True)
        import time
        self._time = time.monotonic

    def _sethint(self, v):
        self._hint = float(v)
        self.update()

    def has_ink(self) -> bool:
        return bool(self.strokes)

    def set_ink(self, color: str):
        self.ink = color
        self.update()

    def clear(self):
        self.strokes.clear()
        self._fade_hint(1.0)
        self.changed.emit(False)
        self.update()

    def undo(self):
        if self.strokes:
            self.strokes.pop()
            if not self.strokes:
                self._fade_hint(1.0)
            self.changed.emit(bool(self.strokes))
            self.update()

    def _fade_hint(self, to: float):
        self._hint_anim.stop(); self._hint_anim.setStartValue(self._hint); self._hint_anim.setEndValue(to); self._hint_anim.start()

    def mousePressEvent(self, e):
        if e.button() != Qt.MouseButton.LeftButton:
            return
        pt = e.position()
        self._last_t = self._time()
        self._cur = [(pt.x(), pt.y(), 2.2)]
        self.strokes.append(self._cur)
        self._fade_hint(0.0)
        self.update()

    def mouseMoveEvent(self, e):
        if self._cur is None:
            return
        pt = e.position()
        x0, y0, w0 = self._cur[-1]
        now = self._time()
        dist = ((pt.x() - x0) ** 2 + (pt.y() - y0) ** 2) ** 0.5
        if dist < 0.8:
            return
        speed = dist / max(now - self._last_t, 1e-3)  # px/s
        target = max(1.3, min(3.6, 3.8 - speed / 700.0))
        w = w0 * 0.7 + target * 0.3
        self._cur.append((pt.x(), pt.y(), w))
        self._last_t = now
        self.update()

    def mouseReleaseEvent(self, e):
        if self._cur is not None:
            self._cur = None
            self.changed.emit(True)

    def _draw_strokes(self, p: QPainter, scale: float = 1.0, color: str | None = None):
        pen = QPen(QColor(color or self.ink))
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        for s in self.strokes:
            if len(s) == 1:
                x, y, w = s[0]
                p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(color or self.ink))
                p.drawEllipse(QPointF(x * scale, y * scale), w * scale / 2, w * scale / 2)
                continue
            for a, b in zip(s, s[1:]):
                pen.setWidthF((a[2] + b[2]) / 2 * scale)
                p.setPen(pen)
                p.drawLine(QPointF(a[0] * scale, a[1] * scale), QPointF(b[0] * scale, b[1] * scale))

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        path = QPainterPath(); path.addRoundedRect(r, 14, 14)
        p.fillPath(path, QColor("#FBFBFD"))
        p.setPen(QPen(QColor("#C9CDDF"), 1, Qt.PenStyle.DashLine))
        y = r.bottom() - 38
        p.drawLine(QPointF(r.left() + 18, y), QPointF(r.right() - 18, y))
        p.setPen(QColor(120, 126, 150, int(200 * self._hint)))
        f = self.font(); f.setPointSize(11); p.setFont(f)
        p.drawText(r.adjusted(0, 0, 0, -8), Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom, tr("pad_line"))
        if self._hint > 0:
            p.setPen(QColor(120, 126, 150, int(110 * self._hint)))
            f.setPointSize(10); p.setFont(f)
            p.drawText(r.adjusted(0, 14, 0, 0), Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, tr("pad_hint"))
        p.setClipPath(path)
        self._draw_strokes(p)
        p.setClipping(False)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor(P["border"]), 1))
        p.drawRoundedRect(r, 14, 14)

    def to_image(self) -> QImage | None:
        """PNG transparente recortado al trazo, a 4× para nitidez."""
        if not self.strokes:
            return None
        pts = [(x, y, w) for s in self.strokes for x, y, w in s]
        pad = 6
        x0 = min(x - w for x, y, w in pts) - pad; x1 = max(x + w for x, y, w in pts) + pad
        y0 = min(y - w for x, y, w in pts) - pad; y1 = max(y + w for x, y, w in pts) + pad
        k = 4.0
        img = QImage(int((x1 - x0) * k), int((y1 - y0) * k), QImage.Format.Format_ARGB32_Premultiplied)
        img.fill(Qt.GlobalColor.transparent)
        p = QPainter(img)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.translate(-x0 * k, -y0 * k)
        self._draw_strokes(p, k)
        p.end()
        return img

    def wipe(self):
        self.strokes.clear()
        self._cur = None
        self.update()


class ToggleSwitch(QPushButton):
    """Interruptor animado (estilo iOS) con etiqueta."""

    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(32)
        self._t = 0.0
        self._anim = QVariantAnimation(self, duration=200)
        self._anim.valueChanged.connect(self._set)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.toggled.connect(self._go)

    def _set(self, v):
        self._t = float(v)
        self.update()

    def _go(self, on: bool):
        self._anim.stop(); self._anim.setStartValue(self._t); self._anim.setEndValue(1.0 if on else 0.0); self._anim.start()

    def sizeHint(self):
        return QSize(self.fontMetrics().horizontalAdvance(self.text()) + 60, 32)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        track = QRectF(1, (self.height() - 22) / 2, 40, 22)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(mix(P["border"], P["accent"], self._t))
        p.drawRoundedRect(track, 11, 11)
        p.setBrush(QColor("#FFFFFF"))
        p.drawEllipse(QPointF(track.left() + 11 + 18 * self._t, track.center().y()), 8.5, 8.5)
        if self.hasFocus():
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(QColor(P["accent"]), 1.5))
            p.drawRoundedRect(track.adjusted(-2, -2, 2, 2), 13, 13)
        p.setPen(QColor(P["text"]))
        f = self.font(); f.setWeight(f.Weight.Medium); p.setFont(f)
        p.drawText(QRectF(52, 0, self.width() - 52, self.height()), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, self.text())
