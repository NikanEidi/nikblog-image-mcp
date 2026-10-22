import mimetypes
import os
import secrets
from pathlib import Path
import boto3

def upload_image(local_path: Path) -> str:
    extension = local_path.suffix
    random_name = secrets.token_hex(16)
    key = f"{random_name}{extension}"
    file_bytes = local_path.read_bytes()

    # Guess the real content type from the extension (image/png, video/mp4,
    # etc.) instead of hardcoding one -- S3 serves this as the real
    # Content-Type header, which matters for video playback even though
    # the frontend itself decides image-vs-video from the URL extension,
    # not this header. Falls back to a generic binary type for anything
    # mimetypes doesn't recognize, rather than lying about what it is.
    content_type, _ = mimetypes.guess_type(local_path.name)
    if content_type is None:
        content_type = "application/octet-stream"

    s3 = boto3.client("s3", region_name=os.environ["AWS_REGION"])
    s3.put_object(
        Bucket=os.environ["S3_BUCKET_NAME"],
        Key=key,
        Body=file_bytes,
        ContentType=content_type,
    )

    bucket = os.environ["S3_BUCKET_NAME"]
    region = os.environ["AWS_REGION"]
    return f"https://{bucket}.s3.{region}.amazonaws.com/{key}"