import uuid

from django.conf import settings

from .image_compressor import compress_profile_image
from .s3_uploader import upload_bytes_to_s3


def save_profile_image(user_id: int, uploaded_file) -> str:
    data, content_type, ext = compress_profile_image(
        uploaded_file,
        max_bytes=settings.PROFILE_IMAGE_MAX_BYTES,
    )
    key = f"{user_id}/profile/{uuid.uuid4().hex}.{ext}"
    upload_bytes_to_s3(
        data=data,
        key=key,
        content_type=content_type,
    )
    return key
