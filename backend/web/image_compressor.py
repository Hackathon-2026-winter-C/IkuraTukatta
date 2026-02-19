from io import BytesIO
from PIL import Image, ImageOps


def compress_profile_image(uploaded_file, max_bytes=3 * 1024 * 1024):
    """
    return: (data: bytes, content_type: str, ext: str)
    """
    raw = uploaded_file.read()
    uploaded_file.seek(0)

    content_type = uploaded_file.content_type or "application/octet-stream"
    ext = uploaded_file.name.rsplit(".", 1)[-1].lower() if "." in uploaded_file.name else "bin"
    if ext == "jpeg":
        ext = "jpg"

    # 3MB以下ならそのまま使う
    if len(raw) <= max_bytes:
        return raw, content_type, ext

    # 3MB超なら圧縮
    image = Image.open(BytesIO(raw))
    image = ImageOps.exif_transpose(image)

    if image.mode != "RGB":
        if "A" in image.getbands():
            bg = Image.new("RGB", image.size, (255, 255, 255))
            bg.paste(image, mask=image.getchannel("A"))
            image = bg
        else:
            image = image.convert("RGB")

    if max(image.size) > 2048:
        image.thumbnail((2048, 2048), Image.LANCZOS)

    best = None
    for quality in (85, 75, 65, 55, 45):
        buf = BytesIO()
        image.save(buf, format="JPEG", quality=quality, optimize=True, progressive=True)
        data = buf.getvalue()
        best = data
        if len(data) <= max_bytes:
            return data, "image/jpeg", "jpg"

    return best, "image/jpeg", "jpg"
