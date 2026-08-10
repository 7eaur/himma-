import os
import boto3
from botocore.exceptions import ClientError
from fastapi import UploadFile
import uuid

S3_ENDPOINT = os.getenv("S3_ENDPOINT", "http://localhost:9000")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "minioadmin")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "minioadmin")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "himma-audio")

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

def upload_audio(file: UploadFile) -> tuple[str, int]:
    """Uploads file to S3 and returns (storage_key, file_size)."""
    key = f"audio/{uuid.uuid4()}_{file.filename}"
    s3_client.upload_fileobj(
        file.file,
        S3_BUCKET_NAME,
        key,
        ExtraArgs={"ContentType": file.content_type}
    )
    # Get file size
    response = s3_client.head_object(Bucket=S3_BUCKET_NAME, Key=key)
    return key, response['ContentLength']

# Initialize bucket on load
try:
    init_storage()
except Exception as e:
    print(f"Warning: Could not initialize S3 storage: {e}")
