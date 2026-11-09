"""Cliente del proceso de render: el proceso principal NUNCA carga MuPDF (ver render_worker.py).

Mantiene la API de antes (`page_count`, `data`, `size`, `render`, `to_pdf_box`, `close`).
"""
from __future__ import annotations

import socket
import struct
import contextlib
import subprocess  # nosec B404 - solo para lanzar el worker de render
import sys

from .render_worker import HDR, MAX_PIXELS, OP_OPEN, OP_QUIT, OP_RENDER, ST_OK, recv_exact, send_frame
from .security import InputRejected, clean_env, interpreter_paths

_KEYS = {"err_pdf_invalid", "err_pdf_encrypted", "err_pdf_pages", "err_render"}
OPEN_TIMEOUT, RENDER_TIMEOUT = 60.0, 30.0


class PdfDoc:
    def __init__(self, data: bytes):
        self.data = data
        self.page_count = 0
        self._pages: list[tuple[float, ...]] = []
        self._proc: subprocess.Popen | None = None
        self._sock: socket.socket | None = None
        self._spawn()
        payload = self._call(OP_OPEN, data, OPEN_TIMEOUT)
        (self.page_count,) = struct.unpack_from("!I", payload)
        for i in range(self.page_count):
            self._pages.append(struct.unpack_from("!8d", payload, 4 + 64 * i))

    # ---- proceso hijo ----
    def _spawn(self) -> None:
        parent, child = socket.socketpair()
        code = f"import sys; sys.path[:0] = {interpreter_paths()!r}; from tuxsign.render_worker import serve; serve({child.fileno()})"
        try:
            self._proc = subprocess.Popen(  # nosec B603 - ejecutable e instrucciones fijos, sin shell
                [sys.executable, "-I", "-B", "-c", code], pass_fds=(child.fileno(),), close_fds=True,
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                env={k: v for k, v in clean_env().items() if k in ("LD_LIBRARY_PATH", "LANG", "LC_ALL")},
                start_new_session=True,
            )
        except OSError as exc:
            parent.close()
            raise InputRejected("err_render") from exc
        finally:
            child.close()
        self._sock = parent

    def _call(self, op: int, payload: bytes, timeout: float) -> bytes:
        if self._sock is None:
            raise InputRejected("err_render")
        try:
            self._sock.settimeout(timeout)
            send_frame(self._sock, op, payload)
            status, n = HDR.unpack(recv_exact(self._sock, HDR.size))
            body = recv_exact(self._sock, n) if n else b""
        except (OSError, ConnectionError, struct.error) as exc:  # worker caído, bloqueado o protocolo roto
            self.close()
            raise InputRejected("err_render") from exc
        if status != ST_OK:
            key = body.decode("ascii", "ignore")
            self.close()
            raise InputRejected(key if key in _KEYS else "err_render")
        return body

    def close(self) -> None:
        sock, proc, self._sock, self._proc = self._sock, self._proc, None, None
        if sock is not None:
            try:
                sock.settimeout(1.0)
                send_frame(sock, OP_QUIT)
            except OSError:
                pass
            sock.close()
        if proc is not None:
            try:
                proc.wait(timeout=1.0)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()

    def __del__(self):
        with contextlib.suppress(Exception):
            self.close()

    # ---- API ----
    def size(self, i: int) -> tuple[float, float]:
        return self._pages[i][0], self._pages[i][1]

    def render(self, i: int, scale: float):
        """Devuelve (samples, width, height, stride) RGB888."""
        if not 0 <= i < self.page_count:
            raise InputRejected("err_render")
        w, h = self.size(i)
        if w * scale * h * scale > MAX_PIXELS:
            scale = (MAX_PIXELS / (w * h)) ** 0.5
        body = self._call(OP_RENDER, struct.pack("!Id", i, scale), RENDER_TIMEOUT)
        pw, ph, stride = struct.unpack_from("!III", body)
        if len(body) != 12 + stride * ph or stride < pw * 3:
            self.close()
            raise InputRejected("err_render")
        return body[12:], pw, ph, stride

    def to_pdf_box(self, i: int, x0: float, y0: float, x1: float, y1: float) -> tuple[float, float, float, float]:
        """Rect en espacio de página visible (pt, origen arriba-izq) → espacio de usuario PDF (origen abajo-izq)."""
        a, b, c, d, e, f = self._pages[i][2:8]
        det = a * d - b * c
        ia, ib, ic, id_ = d / det, -b / det, -c / det, a / det
        ie, if_ = (c * f - d * e) / det, (b * e - a * f) / det
        pts = [(ia * x + ic * y + ie, ib * x + id_ * y + if_) for x, y in ((x0, y0), (x1, y0), (x0, y1), (x1, y1))]
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        return min(xs), min(ys), max(xs), max(ys)
