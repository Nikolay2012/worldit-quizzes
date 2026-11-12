import base64
from io import BytesIO
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers.pil import RoundedModuleDrawer
from qrcode.image.styles.colormasks import SolidFillColorMask


QR_COLOR = (54, 39, 54)
QR_BACKGROUND = (255, 255, 255)


def make_qr_image(url):
    qr = qrcode.QRCode(
        error_correction = qrcode.constants.ERROR_CORRECT_H,
        box_size = 20,
        border = 0,
    )

    qr.add_data(url)

    image = qr.make_image(
        image_factory = StyledPilImage,
        module_drawer = RoundedModuleDrawer(),
        eye_drawer = RoundedModuleDrawer(radius_ratio = 1),
        color_mask = SolidFillColorMask(back_color = QR_BACKGROUND, front_color = QR_COLOR),
    )

    buffer = BytesIO()
    image.save(buffer, format = "PNG")

    encoded = base64.b64encode(buffer.getvalue()).decode()

    return f"data:image/png;base64,{encoded}"