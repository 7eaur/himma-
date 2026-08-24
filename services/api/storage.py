import os
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import UploadFile
import uuid

MAX_AUDIO_BYTES = 10 * 1024 * 1024

S3_ENDPOINT = os.getenv("S3_ENDPOINT", "http://localhost:9000")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "himma-audio")

if not S3_ACCESS_KEY or not S3_SECRET_KEY:
    raise RuntimeError("S3_ACCESS_KEY and S3_SECRET_KEY are required")

s3_client = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY,
)

def init_storage():
    try:
        s3_client.head_bucket(Bucket=S3_BUCKET_NAME)
    except ClientError:
        s3_client.create_bucket(Bucket=S3_BUCKET_NAME)

def upload_audio(file: UploadFile, owner_id: int) -> tuple[str, int]:
    """Uploads file to S3 and returns (storage_key, file_size)."""
    extension = ".webm" if "webm" in (file.content_type or "") else ".audio"
    key = f"audio/{owner_id}/{uuid.uuid4()}{extension}"
    s3_client.upload_fileobj(
        file.file,
        S3_BUCKET_NAME,
        key,
        ExtraArgs={"ContentType": file.content_type}
    )
    # Get file size
    response = s3_client.head_object(Bucket=S3_BUCKET_NAME, Key=key)
    file_size = response['ContentLength']
    if file_size <= 0 or file_size > MAX_AUDIO_BYTES:
        s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=key)
        raise ValueError("Audio file size is outside the allowed range")
    return key, file_size


def verify_audio(storage_key: str, expected_size: int, expected_mime: str) -> None:
    """Verify client-submitted audio metadata against the private object store."""
    try:
        response = s3_client.head_object(Bucket=S3_BUCKET_NAME, Key=storage_key)
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code")
        if error_code in {"404", "NoSuchKey", "NotFound"}:
            raise ValueError("Audio object does not exist") from exc
        raise RuntimeError("Audio storage is unavailable") from exc
    except BotoCoreError as exc:
        raise RuntimeError("Audio storage is unavailable") from exc

    if response["ContentLength"] != expected_size:
        raise ValueError("Audio file size does not match the stored object")
    if response.get("ContentType") != expected_mime:
        raise ValueError("Audio MIME type does not match the stored object")
