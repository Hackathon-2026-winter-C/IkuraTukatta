import boto3
from django.conf import settings


def upload_bytes_to_s3(*, data: bytes, key: str, content_type: str) -> str:
    s3 = boto3.client(
        "s3",
        region_name=settings.AWS_S3_REGION_NAME,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )
    s3.put_object(
        Bucket=settings.AWS_STORAGE_BUCKET_NAME,
        Key=key,
        Body=data,
        ContentType=content_type,
        Tagging="Project=hackathon-winter-c"
    )
    return key
