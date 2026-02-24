# backend/web/receipt_image_service.py
from io import BytesIO
from PIL import Image, ImageOps, UnidentifiedImageError

ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp"}

def compress_and_resize_receipt(uploaded_file, *, max_side=700, max_bytes=1_000_000):
    if (uploaded_file.content_type or "").lower() not in ALLOWED_MIME:
        raise ValueError("unsupported_image_type")

    try:
        img = Image.open(uploaded_file)
    except UnidentifiedImageError:
        raise ValueError("invalid_image")

    # 向きを補正
    img = ImageOps.exif_transpose(img).convert("RGB")

    # 比率を維持して縮小
    img.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
    base_w, base_h = img.size

    quality = 85
    scale = 1.0

    while True:
        work = img
        if scale < 1.0:
            work = img.resize(
                (max(1, int(base_w * scale)), max(1, int(base_h * scale))),
                Image.Resampling.LANCZOS,
            )

        buf = BytesIO()
        work.save(buf, format="JPEG", quality=quality, optimize=True)
        data = buf.getvalue()

        if len(data) <= max_bytes:
            return data, {
                "content_type": "image/jpeg",
                "width": work.width,
                "height": work.height,
                "size": len(data),
            }

        if quality > 55:
            quality -= 5
            continue
        if scale > 0.5:
            scale *= 0.9
            quality = 80
            continue

        raise ValueError("image_too_large")
