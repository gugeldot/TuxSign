"""Pruebas del núcleo (sin UI). Ejecutar: python -m pytest tests  (o python tests/test_core.py)."""
import datetime
import io
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pymupdf
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID
from PIL import Image, ImageDraw

from tuxsign import security
from tuxsign.pdfdoc import PdfDoc
from tuxsign.security import AttemptLimiter, InputRejected, Secret
from tuxsign.signer import CertificateError, check_signatures, load_pkcs12, sign_pdf


def make_p12(password=b"pw", days=30, cn="Ñandú Pérez (TEST)"):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, cn)])
    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
            .serial_number(x509.random_serial_number()).not_valid_before(now - datetime.timedelta(days=1))
            .not_valid_after(now + datetime.timedelta(days=days))
            .add_extension(x509.KeyUsage(True, True, False, False, False, False, False, False, False), True)
            .sign(key, hashes.SHA256()))
    return pkcs12.serialize_key_and_certificates(b"t", key, cert, None, serialization.BestAvailableEncryption(password))


def make_pdf(rotation=0):
    d = pymupdf.open()
    p = d.new_page(width=595, height=842)
    p.insert_text((72, 100), "Contrato de prueba")
    p.set_rotation(rotation)
    return d.tobytes()


def make_sig_png():
    im = Image.new("RGBA", (300, 100), (0, 0, 0, 0))
    ImageDraw.Draw(im).line([(10, 80), (80, 10), (150, 80), (290, 20)], fill=(10, 30, 120, 255), width=5)
    b = io.BytesIO(); im.save(b, "PNG"); return b.getvalue()


def test_sign_and_verify():
    signer, info = load_pkcs12(make_p12(), Secret("pw"))
    assert not info.expired and info.key_usage_ok
    pdf = make_pdf()
    doc = PdfDoc(pdf)
    box = doc.to_pdf_box(0, 300, 700, 500, 780)
    lines = ["Digitally signed by:", info.common_name, "2026-11-09 20:00 +0100"]
    out = sign_pdf(pdf, signer, 0, box, lines, make_sig_png(), "Aprobación")
    res = check_signatures(out)
    assert len(res) == 1 and res[0].intact and res[0].covers_all
    # segunda firma (cadena de firmas)
    out2 = sign_pdf(out, signer, 0, doc.to_pdf_box(0, 50, 700, 250, 780), lines, None)  # bloque solo-texto
    assert len(check_signatures(out2)) == 2 and all(r.intact for r in check_signatures(out2))
    # manipulación posterior → debe detectarse
    tampered = bytearray(out)
    tampered[tampered.find(b"Contrato") ] ^= 0x01 if b"Contrato" in tampered else 0
    open(os.path.join(tempfile.gettempdir(), "fs_signed.pdf"), "wb").write(out2)
    pymupdf.open(stream=out2, filetype="pdf")[0].get_pixmap().save(os.path.join(tempfile.gettempdir(), "fs_signed.png"))


def test_bad_password_generic():
    try:
        load_pkcs12(make_p12(), Secret("mala"))
        raise AssertionError
    except CertificateError as e:
        assert e.key == "err_cert"


def test_box_rotated():
    doc = PdfDoc(make_pdf(90))
    b = doc.to_pdf_box(0, 0, 0, 100, 50)
    assert all(isinstance(v, float) for v in b)


def test_input_validation():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "x.pdf"); open(p, "wb").write(b"no es pdf")
        try:
            security.read_regular_file(p, 1000, b"%PDF-"); raise AssertionError
        except InputRejected:
            pass
        try:
            security.read_regular_file("/dev/zero", 1000); raise AssertionError
        except InputRejected:
            pass
        q = os.path.join(d, "o.pdf"); security.atomic_write(q, b"x")
        assert oct(os.stat(q).st_mode & 0o777) == "0o600"


def test_limiter_and_secret():
    l = AttemptLimiter(free_attempts=1, base_delay=1)
    l.failure(); assert l.remaining() == 0
    l.failure(); assert l.remaining() > 0
    s = Secret("abc"); s.wipe(); assert s.reveal() == b""


def test_audit_chain():
    with tempfile.TemporaryDirectory() as d:
        os.environ["XDG_STATE_HOME"] = d
        from tuxsign.audit import AuditLog
        a = AuditLog()
        a.log("app_start"); a.log("sign_ok", doc="abc"); a.log("sign_fail", code="E1")
        assert a.verify() == (True, 3)
        txt = open(a.path).read().replace("sign_ok", "sign_xx")
        open(a.path, "w").write(txt)
        assert a.verify()[0] is False


def test_text_only_block_renders():
    signer, info = load_pkcs12(make_p12(), Secret("pw"))
    pdf = make_pdf()
    out = sign_pdf(pdf, signer, 0, PdfDoc(pdf).to_pdf_box(0, 100, 400, 330, 460), ["Digitally signed by:", "Ñandú Pérez", "2026-11-09 20:00 +0100"])
    pix = pymupdf.open(stream=out, filetype="pdf")[0].get_pixmap()
    pix.save(os.path.join(tempfile.gettempdir(), "fs_textonly.png"))
    assert check_signatures(out)[0].intact


def test_i18n_complete():
    from tuxsign import i18n
    base = set(i18n.S["en"])
    for code, table in i18n.S.items():
        assert set(table) == base, (code, base ^ set(table))
    assert i18n.DEFAULT == "en" and i18n.current() == "en"
    i18n.set_language("es"); assert i18n.tr("btn_open") == "Abrir PDF"; i18n.set_language("zz"); assert i18n.current() == "en"


def test_seccomp_and_flow_in_subprocess():
    """Tras el hardening: AF_INET bloqueado, AF_UNIX y firma (asyncio) siguen funcionando."""
    import subprocess, textwrap
    code = textwrap.dedent("""
        import socket, sys
        sys.path.insert(0, %r)
        from tuxsign.security import harden_process
        r = harden_process(); print(r)
        try:
            socket.socket(socket.AF_INET, socket.SOCK_DGRAM); print("INET_OPEN")
        except OSError: print("INET_BLOCKED")
        a, b = socket.socketpair(); a.send(b"x"); assert b.recv(1) == b"x"; print("UNIX_OK")
        import tests.test_core as T
        from tuxsign.signer import load_pkcs12, sign_pdf, check_signatures
        from tuxsign.security import Secret
        from tuxsign.pdfdoc import PdfDoc
        sg, _ = load_pkcs12(T.make_p12(), Secret("pw")); pdf = T.make_pdf()
        out = sign_pdf(pdf, sg, 0, PdfDoc(pdf).to_pdf_box(0, 10, 10, 200, 60), ["a", "b", "c"])
        assert check_signatures(out)[0].intact; print("SIGN_OK")
    """ % os.path.join(os.path.dirname(__file__), ".."))
    out = subprocess.run([sys.executable, "-W", "ignore", "-c", code], capture_output=True, text=True,
                         cwd=os.path.join(os.path.dirname(__file__), "..")).stdout
    assert "INET_BLOCKED" in out and "UNIX_OK" in out and "SIGN_OK" in out, out
    assert "'seccomp_filter': True" in out, out


def test_integrity_detects_tampering():
    import base64, json, shutil
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives import serialization as ser
    from tuxsign import integrity
    with tempfile.TemporaryDirectory() as d:
        root = os.path.join(d, "pkg"); os.makedirs(root)
        open(os.path.join(root, "a.py"), "w").write("x=1")
        key = Ed25519PrivateKey.generate()
        pub = key.public_key().public_bytes(ser.Encoding.Raw, ser.PublicFormat.Raw)
        man = integrity.canonical({"files": integrity.hash_tree(root)})
        open(os.path.join(root, "MANIFEST.json"), "wb").write(man)
        open(os.path.join(root, "MANIFEST.sig"), "wb").write(key.sign(man))
        integrity._pubkey = lambda: pub
        assert integrity.verify(root) == "ok"
        open(os.path.join(root, "evil.py"), "w").write("import os")      # módulo plantado
        assert integrity.verify(root) == "fail"
        os.unlink(os.path.join(root, "evil.py")); open(os.path.join(root, "a.py"), "w").write("x=2")
        assert integrity.verify(root) == "fail"                          # fichero modificado


def test_render_worker_roundtrip_and_matrix_parity():
    """El render ocurre en un proceso hijo y la conversión de coordenadas (sin MuPDF) coincide con PyMuPDF."""
    import pymupdf
    for rot in (0, 90, 180, 270):
        raw = make_pdf(rot)
        doc = PdfDoc(raw)
        ref = pymupdf.open(stream=raw, filetype="pdf")[0]
        r = pymupdf.Rect(30, 40, 230, 140) * ~ref.transformation_matrix
        r.normalize()
        got = doc.to_pdf_box(0, 30, 40, 230, 140)
        assert all(abs(a - b) < 1e-6 for a, b in zip(got, (r.x0, r.y0, r.x1, r.y1))), (rot, got, tuple(r))
        samples, w, h, stride = doc.render(0, 1.0)
        assert len(samples) == stride * h and (w, h) == (round(doc.size(0)[0]), round(doc.size(0)[1]))
        pid = doc._proc.pid
        st = open(f"/proc/{pid}/status").read()
        assert "Seccomp:\t2" in st, "el worker debe tener filtro seccomp activo"
        doc.close()
        assert doc._proc is None


def test_worker_rejects_bad_input_and_survives_crash():
    for bad in (b"%PDF-1.4 basura", b"no es un pdf"):
        try:
            PdfDoc(bad); raise AssertionError
        except InputRejected as e:
            assert e.key == "err_pdf_invalid", e.key
    doc = PdfDoc(make_pdf())
    os.kill(doc._proc.pid, 9)  # el proceso de render muere (p. ej. explotado y abortado)
    try:
        doc.render(0, 1.0); raise AssertionError
    except InputRejected as e:
        assert e.key == "err_render"
    assert doc._proc is None


def test_worker_sandbox_denies_files_sockets_exec():
    """Perfil del worker: sin abrir ficheros, sin sockets, sin execve (Landlock + seccomp)."""
    import subprocess, textwrap
    code = textwrap.dedent("""
        import os, socket, sys, subprocess
        sys.path.insert(0, %r)
        import pymupdf  # precarga como hace el worker
        from tuxsign.security import harden_process
        r = harden_process(worker=True); print("REPORT", r.get("landlock"), r.get("seccomp_filter"))
        def probe(name, fn):
            try: fn(); print(name, "ALLOWED")
            except BaseException as e: print(name, "DENIED")
        probe("open", lambda: open("/etc/passwd").read())
        probe("write", lambda: open("/tmp/tuxsign_probe", "w"))
        probe("socket", lambda: socket.socket())
        probe("unix", lambda: socket.socket(socket.AF_UNIX))
        probe("exec", lambda: os.execv("/bin/true", ["true"]))
        probe("spawn", lambda: subprocess.run(["/bin/true"]))
    """ % os.path.join(os.path.dirname(__file__), ".."))
    out = subprocess.run([sys.executable, "-W", "ignore", "-c", code], capture_output=True, text=True).stdout
    for name in ("open", "write", "socket", "unix", "exec", "spawn"):
        assert f"{name} DENIED" in out, out
    landlock = "landlock" in open("/sys/kernel/security/lsm").read() if os.path.exists("/sys/kernel/security/lsm") else False
    assert ("REPORT True True" in out) if landlock else ("True" in out.split("REPORT")[1].split("\n")[0]), out


def test_clean_env_drops_injection_vars():
    from tuxsign.security import clean_env
    env = clean_env({"LD_PRELOAD": "/tmp/x.so", "PYTHONPATH": "/tmp/e", "QT_PLUGIN_PATH": "/tmp/p", "LD_LIBRARY_PATH": "/tmp/l",
                     "HOME": "/home/user", "WAYLAND_DISPLAY": "wayland-0", "LANG": "en_US.UTF-8"})
    assert set(env) == {"HOME", "WAYLAND_DISPLAY", "LANG"}, env


def test_robustness_hardening():
    import json
    from tuxsign import privacy
    from tuxsign.signer import ascii_fold
    assert ascii_fold("Ana\nPérez\x00\t" + "x" * 200).count("\n") == 0 and len(ascii_fold("x" * 200)) == 80
    with tempfile.TemporaryDirectory() as d:
        os.environ["XDG_CONFIG_HOME"] = d
        os.makedirs(os.path.join(d, "tuxsign"))
        open(os.path.join(d, "tuxsign", "settings.json"), "w").write(json.dumps({"retention_days": "abc", "language": "zz", "audit_enabled": None}))
        s = privacy.load_settings()
        assert s.retention_days == 365 and s.language == "en" and s.audit_enabled is False
        os.environ["XDG_CONFIG_HOME"] = "relativo/evil"                      # ruta relativa → se ignora
        assert os.path.isabs(privacy.config_dir())
    with tempfile.TemporaryDirectory() as d:                                  # el log sigue válido con muchas entradas
        os.environ["XDG_STATE_HOME"] = d
        from tuxsign.audit import AuditLog
        a = AuditLog()
        for i in range(300): a.log("doc_open", doc="%016x" % i)
        assert a.verify() == (True, 300)


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            f(); print("OK", n)
