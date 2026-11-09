"""Firma PAdES con certificados PKCS#12 (pyHanko). Sin red ni sellado de tiempo externo.

La firma criptográfica (CMS/PAdES-B-B, SHA-256) cubre todo el documento mediante actualización
incremental. La apariencia visible es un bloque "Firmado digitalmente por ... / fecha", con firma
manuscrita opcional.
"""
from __future__ import annotations

import io
import logging
import unicodedata
import uuid
from dataclasses import dataclass
from fractions import Fraction
from datetime import datetime, timezone

from asn1crypto import keys as akeys
from asn1crypto import x509 as a509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import pkcs12
from PIL import Image
from pyhanko.pdf_utils import images
from pyhanko.pdf_utils.font.basic import SimpleFontEngineFactory
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.pdf_utils.layout import AxisAlignment, Margins, SimpleBoxLayoutRule
from pyhanko.pdf_utils.reader import PdfFileReader
from pyhanko.pdf_utils.text import TextBoxStyle
from pyhanko.sign import signers
from pyhanko.sign.fields import SigFieldSpec, SigSeedSubFilter
from pyhanko.sign.validation import validate_pdf_signature
from pyhanko.stamp import TextStampStyle
from pyhanko_certvalidator.registry import SimpleCertificateStore

from .security import Secret

# RGPD/A.8.15: las librerías pueden volcar nombres del titular en sus logs, así que se silencian.
for _name in ("pyhanko", "pyhanko_certvalidator"):
    logging.getLogger(_name).setLevel(logging.CRITICAL)
    logging.getLogger(_name).propagate = False

IMAGE_TEXT_PT = 22  # franja de texto bajo la firma manuscrita (pt)


class AppError(Exception):
    """Error con clave i18n (la UI lo traduce, nunca hay texto fijo ni detalles internos)."""

    def __init__(self, key: str, **kw):
        super().__init__(key)
        self.key, self.kw = key, kw


class CertificateError(AppError):
    pass


class SigningFailed(AppError):
    pass


@dataclass(frozen=True)
class CertInfo:
    common_name: str
    issuer: str
    not_after: datetime
    expired: bool
    key_usage_ok: bool


@dataclass(frozen=True)
class SigCheck:
    field: str
    signer: str
    intact: bool
    covers_all: bool


def ascii_fold(text: str, max_len: int = 80) -> str:
    """ASCII imprimible de una sola línea (las fuentes estándar PDF no cubren Unicode y el CN no es de confianza)."""
    folded = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    folded = "".join(ch for ch in folded if ch.isprintable())
    return folded[:max_len].strip() or "-"


def load_pkcs12(p12_bytes: bytes, password: Secret) -> tuple[signers.SimpleSigner, CertInfo]:
    try:
        key, cert, extra = pkcs12.load_key_and_certificates(p12_bytes, password.reveal())
    except Exception as exc:  # noqa: BLE001 - no revelar si falló contraseña o formato
        raise CertificateError("err_cert") from exc
    if key is None or cert is None:
        raise CertificateError("err_cert_nokey")
    try:
        key_der = key.private_bytes(serialization.Encoding.DER, serialization.PrivateFormat.PKCS8,
                                    serialization.NoEncryption())
        store = SimpleCertificateStore()
        store.register_multiple([a509.Certificate.load(c.public_bytes(serialization.Encoding.DER)) for c in (extra or [])])
        signer = signers.SimpleSigner(
            signing_cert=a509.Certificate.load(cert.public_bytes(serialization.Encoding.DER)),
            signing_key=akeys.PrivateKeyInfo.load(key_der),
            cert_registry=store,
        )
        del key_der
    except Exception as exc:  # noqa: BLE001
        raise CertificateError("err_cert") from exc

    c = signer.signing_cert
    not_after = c.not_valid_after
    try:
        usage = c.key_usage_value.native if c.key_usage_value else None
        ok = usage is None or bool({"digital_signature", "non_repudiation", "content_commitment"} & set(usage))
    except Exception:  # noqa: BLE001
        ok = True
    info = CertInfo(
        common_name=c.subject.native.get("common_name", c.subject.human_friendly),
        issuer=c.issuer.native.get("common_name", c.issuer.human_friendly),
        not_after=not_after,
        expired=not_after < datetime.now(timezone.utc),
        key_usage_ok=ok,
    )
    return signer, info


def fit_font_size(lines: list[str], width: float, height: float) -> float:
    """Tamaño de fuente (Helvetica) para que las líneas quepan en el bloque (0.5 em de ancho medio)."""
    n = max(1, len(lines))
    by_h = (height - 6) / (n * 1.3)
    by_w = (width - 8) / (0.52 * max(len(x) for x in lines))
    return max(4.0, min(14.0, by_h, by_w))


def sign_pdf(
    pdf_bytes: bytes,
    signer: signers.SimpleSigner,
    page: int,
    box: tuple[float, float, float, float],
    lines: list[str],
    signature_png: bytes | None = None,
    reason: str = "",
) -> bytes:
    """Firma `pdf_bytes`. `box` en puntos PDF (x1, y1, x2, y2), origen abajo-izquierda.

    `lines`: texto del bloque (se pliega a ASCII: fuentes estándar PDF). `signature_png` opcional.
    """
    try:
        ibox = tuple(int(round(v)) for v in box)  # pyHanko opera con racionales, y con enteros se evitan errores de tipo
        w, h = ibox[2] - ibox[0], ibox[3] - ibox[1]
        text_lines = [ascii_fold(x) for x in lines]
        writer = IncrementalPdfFileWriter(io.BytesIO(pdf_bytes), strict=False)
        field = "TuxSign_" + uuid.uuid4().hex[:8]
        text = "\n".join(text_lines).replace("%", "%%")
        font = SimpleFontEngineFactory("Helvetica", 0.52)
        if signature_png:
            img = Image.open(io.BytesIO(signature_png)).convert("RGBA")
            tsize = fit_font_size(text_lines, w, IMAGE_TEXT_PT + 6)
            style = TextStampStyle(
                stamp_text=text,
                text_box_style=TextBoxStyle(font=font, font_size=Fraction(round(tsize * 4), 4)),
                background=images.PdfImage(img),
                background_opacity=1.0,
                background_layout=SimpleBoxLayoutRule(
                    x_align=AxisAlignment.ALIGN_MID, y_align=AxisAlignment.ALIGN_MAX,
                    margins=Margins(left=2, right=2, top=2, bottom=IMAGE_TEXT_PT),
                ),
                inner_content_layout=SimpleBoxLayoutRule(
                    x_align=AxisAlignment.ALIGN_MID, y_align=AxisAlignment.ALIGN_MIN,
                    margins=Margins(left=2, right=2, top=2, bottom=1),
                ),
                border_width=0,
            )
        else:
            style = TextStampStyle(
                stamp_text=text,
                text_box_style=TextBoxStyle(font=font, font_size=Fraction(round(fit_font_size(text_lines, w, h) * 4), 4)),
                inner_content_layout=SimpleBoxLayoutRule(
                    x_align=AxisAlignment.ALIGN_MID, y_align=AxisAlignment.ALIGN_MID,
                    margins=Margins(left=4, right=4, top=3, bottom=3),
                ),
                border_width=1,
            )
        meta = signers.PdfSignatureMetadata(
            field_name=field, md_algorithm="sha256", subfilter=SigSeedSubFilter.PADES, reason=reason[:200] or None,
        )
        pdf_signer = signers.PdfSigner(
            meta, signer=signer, stamp_style=style,
            new_field_spec=SigFieldSpec(sig_field_name=field, on_page=page, box=ibox),
        )
        out = io.BytesIO()
        pdf_signer.sign_pdf(writer, output=out)
        return out.getvalue()
    except Exception as exc:  # noqa: BLE001
        raise SigningFailed("err_sign", code=type(exc).__name__) from exc


def check_signatures(pdf_bytes: bytes) -> list[SigCheck]:
    """Verifica integridad criptográfica de las firmas existentes (no la cadena de confianza)."""
    results: list[SigCheck] = []
    try:
        reader = PdfFileReader(io.BytesIO(pdf_bytes), strict=False)
        for sig in reader.embedded_signatures:
            st = validate_pdf_signature(sig)
            cert = st.signing_cert
            name = cert.subject.native.get("common_name", cert.subject.human_friendly) if cert else "?"
            covers = bool(st.coverage and st.coverage.name == "ENTIRE_FILE")
            results.append(SigCheck(sig.field_name, name, bool(st.intact), covers))
    except Exception:  # noqa: BLE001
        return results
    return results
