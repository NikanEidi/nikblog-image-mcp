import os
import secrets
from pathlib import Path
import boto3

def upload_image(local_path: Path) -> str:
    extension = local_path.suffix
    random_name = secrets.token_hex(16)
    key = f"{random_name}{extension}"
    file_bytes = local_path.read_bytes()

    s3 = boto3.client("s3", region_name=os.environ["AWS_REGION"])
    s3.put_object(
        Bucket=os.environ["S3_BUCKET_NAME"],
        Key=key,
        Body=file_bytes,
        ContentType="image/png",
    )

    bucket = os.environ["S3_BUCKET_NAME"]
    region = os.environ["AWS_REGION"]
    return f"https://{bucket}.s3.{region}.amazonaws.com/{key}"