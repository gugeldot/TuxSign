"""Visor PDF (QGraphicsView) con escena en puntos PDF y sello de firma arrastrable."""
from __future__ import annotations

from PySide6.QtCore import (
    QEasingCurve, QPointF, QPropertyAnimation, QRectF, Qt, QTimer, QVariantAnimation, Signal,
)
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPen, QPixmap, QTransform
from PySide6.QtWidgets import (
    QGraphicsItem, QGraphicsObject, QGraphicsPixmapItem, QGraphicsRectItem, QGraphicsScene, QGraphicsView,
    QStyleOptionGraphicsItem,
)

from ..pdfdoc import PdfDoc
from ..security import InputRejected
from ..signer import IMAGE_TEXT_PT, fit_font_size
from .theme import P, mix

GAP = 24.0
MARGIN = 40.0


class SignatureItem(QGraphicsObject):
    """Bloque de firma "Firmado digitalmente por...": arrastrar, redimensionar y borrar (Supr).

    Con imagen manuscrita el alto sigue la proporción de la imagen, y solo con texto se redimensiona libremente.
    """

    moved = Signal()
    MIN_W, MIN_H = 110.0, 38.0

    def __init__(self, image: QImage | None, lines: list[str], width_pt: float = 200.0):
        super().__init__()
        self.lines = lines
        self.w = width_pt
        self._h = 58.0
        self.pix: QPixmap | None = None
        self.aspect = 0.0
        self.set_content(image, lines)
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemIsFocusable
        )
        self.setAcceptHoverEvents(True)
        self.setZValue(10)
        self._resizing = False
        self._hover = False
        self.setCursor(Qt.CursorShape.SizeAllCursor)

    def set_content(self, image: QImage | None, lines: list[str]) -> None:
        self.prepareGeometryChange()
        self.lines = lines
        if image is not None:
            self.pix = QPixmap.fromImage(image)
            self.aspect = image.height() / image.width()
        else:
            self.pix, self.aspect = None, 0.0
        self.update()

    def set_lines(self, lines: list[str]) -> None:
        if lines != self.lines:
            self.lines = lines
            self.update()

    @property
    def h(self) -> float:
        return self.w * self.aspect + IMAGE_TEXT_PT if self.pix else self._h

    def boundingRect(self) -> QRectF:
        return QRectF(-8, -8, self.w + 16, self.h + 16)

    def stamp_rect(self) -> QRectF:
        return QRectF(self.pos().x(), self.pos().y(), self.w, self.h)

    def _handle_rect(self, lod: float) -> QRectF:
        s = 12 / lod
        return QRectF(self.w - s / 2, self.h - s / 2, s, s)

    def _draw_text(self, p: QPainter, area: QRectF) -> None:
        fs = fit_font_size(self.lines, area.width(), area.height())
        p.save()
        p.scale(0.1, 0.1)  # permite tamaños de fuente fraccionarios (la escena está en puntos PDF)
        f = QFont("Helvetica", 1); f.setStyleHint(QFont.StyleHint.SansSerif); f.setPixelSize(max(1, round(fs * 10)))
        p.setFont(f)
        p.setPen(QColor("#222"))
        big = QRectF(area.x() * 10, area.y() * 10, area.width() * 10, area.height() * 10)
        p.drawText(big, Qt.AlignmentFlag.AlignCenter, "\n".join(self.lines))
        p.restore()

    def paint(self, p: QPainter, opt: QStyleOptionGraphicsItem, _w=None):
        lod = opt.levelOfDetailFromTransform(p.worldTransform())
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        body = QRectF(0, 0, self.w, self.h)
        p.setBrush(QColor(255, 255, 255, 235))
        p.setPen(QPen(QColor(P["accent"]), 1.5 / lod, Qt.PenStyle.DashLine if (self._hover or self.isSelected()) else Qt.PenStyle.SolidLine))
        p.drawRoundedRect(body, 3 / lod, 3 / lod)
        if self.pix:
            p.drawPixmap(QRectF(2, 2, self.w - 4, self.w * self.aspect), self.pix, QRectF(self.pix.rect()))
            self._draw_text(p, QRectF(2, self.h - IMAGE_TEXT_PT, self.w - 4, IMAGE_TEXT_PT - 1))
        else:
            self._draw_text(p, body.adjusted(4, 3, -4, -3))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(P["accent"]))
        p.drawEllipse(self._handle_rect(lod))

    def _lod(self) -> float:
        sc = self.scene()
        return sc.views()[0].transform().m11() if sc and sc.views() else 1.0

    def hoverEnterEvent(self, e):
        self._hover = True; self.update()

    def hoverMoveEvent(self, e):
        self.setCursor(Qt.CursorShape.SizeFDiagCursor if self._handle_rect(self._lod()).adjusted(-6, -6, 6, 6).contains(e.pos())
                       else Qt.CursorShape.SizeAllCursor)

    def hoverLeaveEvent(self, e):
        self._hover = False; self.update()

    def mousePressEvent(self, e):
        self._resizing = self._handle_rect(self._lod()).adjusted(-6, -6, 6, 6).contains(e.pos())
        self.setFocus()
        if not self._resizing:
            super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if self._resizing:
            self.prepareGeometryChange()
            self.w = max(self.MIN_W, min(460.0, e.pos().x()))
            if not self.pix:
                self._h = max(self.MIN_H, min(300.0, e.pos().y()))
            self.update()
            self.moved.emit()
        else:
            super().mouseMoveEvent(e)
            self.moved.emit()

    def mouseReleaseEvent(self, e):
        self._resizing = False
        super().mouseReleaseEvent(e)
        self.moved.emit()

    def keyPressEvent(self, e):
        if e.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            sc = self.scene()
            if sc:
                sc.removeItem(self)
                self.moved.emit()
        else:
            super().keyPressEvent(e)


class PageView(QGraphicsView):
    page_changed = Signal(int, int)  # actual, total
    zoom_changed = Signal(float)
    stamp_changed = Signal()
    render_failed = Signal(str)  # clave i18n del error

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene_ = QGraphicsScene(self)
        self.setScene(self.scene_)
        self.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.SmartViewportUpdate)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setFrameShape(QGraphicsView.Shape.NoFrame)
        self.doc: PdfDoc | None = None
        self.zoom = 1.0
        self._render_zoom: dict[int, float] = {}
        self._pages: list[tuple[QGraphicsRectItem, QGraphicsPixmapItem, float, float]] = []
        self.stamp: SignatureItem | None = None
        self._z_anim = QVariantAnimation(self, duration=220)
        self._z_anim.valueChanged.connect(self._apply_zoom)
        self._z_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._z_anim.finished.connect(self._render_visible)
        self._debounce = QTimer(self, singleShot=True, interval=60)
        self._debounce.timeout.connect(self._render_visible)
        self.verticalScrollBar().valueChanged.connect(lambda _v: (self._debounce.start(), self._emit_page()))

    def clear(self):
        """Vacía el visor (cierre de documento)."""
        self.scene_.clear()
        self._pages.clear()
        self._render_zoom.clear()
        self.stamp = None
        self.doc = None
        self.page_changed.emit(0, 0)

    # ---- carga ----
    def load(self, doc: PdfDoc):
        self.scene_.clear()
        self._pages.clear()
        self._render_zoom.clear()
        self.stamp = None
        self.doc = doc
        y = MARGIN
        maxw = 0.0
        shadows: list[QGraphicsRectItem] = []
        for i in range(doc.page_count):
            w, h = doc.size(i)
            shadow = QGraphicsRectItem(QRectF(4, 6, w, h))
            shadow.setBrush(QColor(0, 0, 0, 70)); shadow.setPen(QPen(Qt.PenStyle.NoPen)); shadow.setPos(0, y)
            paper = QGraphicsRectItem(QRectF(0, 0, w, h)); paper.setBrush(QColor("white")); paper.setPen(QPen(Qt.PenStyle.NoPen))
            paper.setPos(0, y)
            pm = QGraphicsPixmapItem(paper); pm.setTransformationMode(Qt.TransformationMode.SmoothTransformation)
            self.scene_.addItem(shadow); self.scene_.addItem(paper)
            shadows.append(shadow)
            self._pages.append((paper, pm, w, h))
            y += h + GAP
            maxw = max(maxw, w)
        for sh, (paper, _pm, w, _h) in zip(shadows, self._pages):  # centrar
            paper.setX((maxw - w) / 2 + MARGIN)
            sh.setPos(paper.pos())
        self.scene_.setSceneRect(0, 0, maxw + 2 * MARGIN, y + MARGIN - GAP)
        self.fit_width(animated=False)
        self.page_changed.emit(0, doc.page_count)

    # ---- zoom ----
    def _apply_zoom(self, z):
        self.zoom = float(z)
        self.setTransform(QTransform.fromScale(self.zoom, self.zoom))
        self.zoom_changed.emit(self.zoom)

    def set_zoom(self, z: float, animated: bool = True):
        z = max(0.25, min(4.0, z))
        if animated:
            self._z_anim.stop(); self._z_anim.setStartValue(self.zoom); self._z_anim.setEndValue(z); self._z_anim.start()
        else:
            self._apply_zoom(z); self._render_visible()

    def fit_width(self, animated: bool = True):
        if not self._pages:
            return
        w = max(w for _a, _b, w, _c in self._pages)
        self.set_zoom((self.viewport().width() - 60) / w, animated)

    def wheelEvent(self, e):
        if e.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.set_zoom(self.zoom * (1.12 if e.angleDelta().y() > 0 else 1 / 1.12), animated=False)
            e.accept()
        else:
            super().wheelEvent(e)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._debounce.start()

    # ---- render perezoso ----
    def _render_visible(self):
        if not self.doc:
            return
        vis = self.mapToScene(self.viewport().rect()).boundingRect().adjusted(0, -400, 0, 400)
        dpr = self.devicePixelRatioF()
        scale = self.zoom * dpr
        for i, (paper, pm, w, h) in enumerate(self._pages):
            if not paper.sceneBoundingRect().intersects(vis):
                continue
            if abs(self._render_zoom.get(i, 0) - scale) < 0.01:
                continue
            try:
                samples, pw, ph, stride = self.doc.render(i, scale)
            except InputRejected as exc:  # el proceso de render murió o excedió límites
                self.render_failed.emit(exc.key)
                return
            img = QImage(samples, pw, ph, stride, QImage.Format.Format_RGB888).copy()
            pm.setPixmap(QPixmap.fromImage(img))
            pm.setScale(w / pw)  # píxeles → puntos
            self._render_zoom[i] = scale

    def _emit_page(self):
        self.page_changed.emit(self.current_page(), len(self._pages))

    def current_page(self) -> int:
        if not self._pages:
            return 0
        mid = self.mapToScene(self.viewport().rect().center()).y()
        for i, (paper, _pm, _w, h) in enumerate(self._pages):
            if mid < paper.y() + h + GAP / 2:
                return i
        return len(self._pages) - 1

    def goto_page(self, i: int):
        if not self._pages:
            return
        i = max(0, min(len(self._pages) - 1, i))
        target = self._pages[i][0].y() - 16
        anim = QPropertyAnimation(self.verticalScrollBar(), b"value", self)
        anim.setDuration(320)
        anim.setStartValue(self.verticalScrollBar().value())
        anim.setEndValue(int(self.mapFromScene(0, target).y() + self.verticalScrollBar().value()))
        anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)

    # ---- sello ----
    def place_stamp(self, image: QImage | None, lines: list[str]):
        """Coloca el bloque. Si ya existe, lo actualiza conservando posición y tamaño."""
        if self.has_stamp():
            self.stamp.set_content(image, lines)
            self.stamp_changed.emit()
            return
        it = SignatureItem(image, lines)
        it.moved.connect(self.stamp_changed)
        i = self.current_page()
        paper, _pm, w, h = self._pages[i]
        vis = self.mapToScene(self.viewport().rect()).boundingRect()
        cx = paper.x() + w / 2 - it.w / 2
        cy = max(paper.y() + 20, min(paper.y() + h - it.h - 20, vis.center().y() - it.h / 2))
        it.setPos(cx, cy)
        it.setTransformOriginPoint(it.w / 2, it.h / 2)
        self.scene_.addItem(it)
        self.stamp = it
        it.setSelected(True)
        for prop, a_, b_ in ((b"scale", 0.6, 1.0), (b"opacity", 0.0, 1.0)):
            an = QPropertyAnimation(it, prop, it)
            an.setDuration(380); an.setStartValue(a_); an.setEndValue(b_)
            an.setEasingCurve(QEasingCurve.Type.OutBack if prop == b"scale" else QEasingCurve.Type.OutCubic)
            an.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
        self.stamp_changed.emit()

    def remove_stamp(self):
        if self.stamp and self.stamp.scene():
            self.scene_.removeItem(self.stamp)
        self.stamp = None
        self.stamp_changed.emit()

    def has_stamp(self) -> bool:
        return self.stamp is not None and self.stamp.scene() is not None

    def stamp_placement(self) -> tuple[int, QRectF] | None:
        """(página, rect en puntos relativos a la página visible)."""
        if not self.has_stamp():
            return None
        r = self.stamp.stamp_rect()
        c = r.center()
        for i, (paper, _pm, w, h) in enumerate(self._pages):
            pr = QRectF(paper.x(), paper.y(), w, h)
            if pr.contains(c):
                rel = QRectF(r.x() - paper.x(), r.y() - paper.y(), r.width(), r.height())
                rel = rel.intersected(QRectF(0, 0, w, h))
                return i, rel
        return None
