"""Proceso de render PDF con privilegios mínimos (separación de privilegios, ISO 27002 A.8.22 / A.8.27).

Es el ÚNICO proceso que carga PyMuPDF/MuPDF (código C que parsea PDFs no fiables). Si un PDF malicioso lograse ejecutar
código, quedaría dentro de este proceso sin: acceso a ficheros (Landlock), red ni creación de sockets, `execve`,
ni la clave del certificado (vive solo en el proceso principal). Se comunica por un socketpair ya abierto.

Protocolo: petición `!BI` (op, longitud) + payload y respuesta `!BI` (estado, longitud) + payload.
"""
from __future__ import annotations

import resource
import socket
import struct
import sys

OP_OPEN, OP_RENDER, OP_QUIT = 1, 2, 3
ST_OK, ST_ERR = 0, 1
MAX_PIXELS = 120_000_000          # ~360 MB RGB
MAX_PAGE_PT = 20_000.0
HDR = struct.Struct("!BI")


def recv_exact(sock: socket.socket, n: int) -> bytes:
    buf = bytearray(n)
    view, got = memoryview(buf), 0
    while got < n:
        k = sock.recv_into(view[got:], n - got)
        if not k:
            raise ConnectionError("peer closed")
        got += k
    return bytes(buf)


def send_frame(sock: socket.socket, code: int, payload: bytes = b"") -> None:
    sock.sendall(HDR.pack(code, len(payload)) + payload)


def serve(fd: int) -> None:
    # 1) TODO lo que se vaya a necesitar se importa/precalienta ANTES de aplicar el sandbox
    import pymupdf
    from .security import MAX_PDF_BYTES, MAX_PDF_PAGES, harden_process

    pymupdf.TOOLS.mupdf_display_errors(False)
    pymupdf.TOOLS.mupdf_display_warnings(False)
    warm = pymupdf.open()
    warm.new_page().insert_text((10, 20), "x")
    warm[0].get_pixmap()
    warm.close()
    sock = socket.socket(fileno=fd)
    sock.settimeout(None)
    try:
        resource.setrlimit(resource.RLIMIT_AS, (6 << 30, 6 << 30))  # techo de memoria virtual
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    except (ValueError, OSError):
        pass
    # 2) sandbox: sin ficheros, sin sockets nuevos, sin execve, sin ptrace/bpf/mount…
    harden_process(worker=True)

    doc = None
    while True:
        try:
            op, n = HDR.unpack(recv_exact(sock, HDR.size))
            if n > MAX_PDF_BYTES + 64:
                return
            payload = recv_exact(sock, n) if n else b""
        except (ConnectionError, OSError, struct.error):
            return
        try:
            if op == OP_QUIT:
                return
            if op == OP_OPEN and doc is None:
                doc = pymupdf.open(stream=payload, filetype="pdf")
                if doc.needs_pass or doc.is_encrypted:
                    send_frame(sock, ST_ERR, b"err_pdf_encrypted"); return
                if not 1 <= doc.page_count <= MAX_PDF_PAGES:
                    send_frame(sock, ST_ERR, b"err_pdf_pages"); return
                out = bytearray(struct.pack("!I", doc.page_count))
                for i in range(doc.page_count):
                    pg = doc[i]
                    r, m = pg.rect, pg.transformation_matrix
                    if not (1.0 <= r.width <= MAX_PAGE_PT and 1.0 <= r.height <= MAX_PAGE_PT):
                        send_frame(sock, ST_ERR, b"err_pdf_invalid"); return
                    out += struct.pack("!8d", r.width, r.height, m.a, m.b, m.c, m.d, m.e, m.f)
                send_frame(sock, ST_OK, bytes(out))
            elif op == OP_RENDER and doc is not None:
                idx, scale = struct.unpack("!Id", payload)
                scale = min(8.0, max(0.1, scale))
                r = doc[idx].rect
                if r.width * scale * r.height * scale > MAX_PIXELS:
                    send_frame(sock, ST_ERR, b"err_render"); continue
                pix = doc[idx].get_pixmap(matrix=pymupdf.Matrix(scale, scale), alpha=False)
                send_frame(sock, ST_OK, struct.pack("!III", pix.width, pix.height, pix.stride) + pix.samples)
            else:
                send_frame(sock, ST_ERR, b"err_render")
        except Exception:  # noqa: BLE001 - nunca propagar detalles internos, el cliente decide
            try:
                send_frame(sock, ST_ERR, b"err_pdf_invalid" if op == OP_OPEN else b"err_render")
            except OSError:
                return
            if op == OP_OPEN:
                return


if __name__ == "__main__":  # no se ejecuta directamente: lo lanza pdfdoc.PdfDoc
    sys.exit("internal module")
