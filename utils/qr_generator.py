"""
QR Code generation utility.
Generates QR codes as base64-encoded PNG strings for embedding in HTML.
"""
import io
import base64
import qrcode
from qrcode.image.pil import PilImage


def generate_qr_base64(data: str, box_size: int = 10, border: int = 4) -> str:
    """
    Generate a QR code from `data` and return a base64-encoded PNG data URI.
    Ready to be used in an <img src="..."> tag.
    """
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img: PilImage = qr.make_image(fill_color='#0f172a', back_color='#f8fafc')

    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)

    b64 = base64.b64encode(buffer.read()).decode('utf-8')
    return f"data:image/png;base64,{b64}"
