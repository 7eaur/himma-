"""
recordings.py — legacy MinIO-backed recording compatibility routes.

The canonical activity/assessment upload path lives in ``storage.py``. These
routes remain mounted for compatibility, so they enforce the same size boundary
before a presigned upload is issued and revalidate the stored object afterward.
Raw object-store exceptions are never exposed to clients.
"""

import logging
import os
import uuid

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from db.models import Student
from dependencies import get_current_researcher, get_current_student
from storage import MAX_AUDIO_BYTES

router = APIRouter(prefix="/recordings", tags=["Recordings"])
logger = logging.getLogger(__name__)

S3_ENDPOINT = os.getenv("S3_ENDPOINT", "http://localhost:9000")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "himma-audio")
UPLOAD_URL_EXPIRY = 900
STREAM_URL_EXPIRY = 300
MIN_AUDIO_BYTES = 1000

if not S3_ACCESS_KEY or not S3_SECRET_KEY:
    raise RuntimeError("S3_ACCESS_KEY and S3_SECRET_KEY are required")


def _get_s3():
    return boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY,
        region_name="us-east-1",
    )


def _storage_unavailable(exc: Exception, *, operation: str) -> HTTPException:
    logger.exception("Recording storage operation failed: %s", operation, exc_info=exc)
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="خدمة حفظ التسجيلات غير متاحة مؤقتًا، حاول مرة أخرى لاحقًا",
    )


class InitRequest(BaseModel):
    file_size: int
    mime_type: str = "audio/webm"


class InitResponse(BaseModel):
    recording_id: str
    upload_url: str
    storage_key: str
    required_headers: dict[str, str]


class CompleteRequest(BaseModel):
    recording_id: str
    storage_key: str


class CompleteResponse(BaseModel):
    status: str
    storage_key: str
    file_size: int
    mime_type: str


class StreamResponse(BaseModel):
    url: str
    expires_in: int


def _validate_audio_metadata(*, file_size: int, mime_type: str) -> None:
    if file_size < MIN_AUDIO_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ملف التسجيل فارغ أو أصغر من الحد المقبول",
        )
    if file_size > MAX_AUDIO_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="حجم التسجيل يتجاوز الحد المسموح",
        )
    if mime_type != "audio/webm":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="نوع ملف التسجيل غير مدعوم",
        )


@router.post("/init", response_model=InitResponse)
def init_recording(
    req: InitRequest,
    student: Student = Depends(get_current_student),
):
    """Issue a PUT URL whose signed headers bind MIME and exact content length.

    A caller must declare the object size before receiving a presigned URL. The
    same ``Content-Length`` and ``Content-Type`` values are part of the signed
    request, so an oversized object cannot use this compatibility URL. The
    object is independently revalidated again on ``/complete``.
    """
    _validate_audio_metadata(file_size=req.file_size, mime_type=req.mime_type)
    recording_id = str(uuid.uuid4())
    storage_key = f"audio/{student.id}/{recording_id}.webm"

    s3 = _get_s3()
    try:
        upload_url = s3.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": S3_BUCKET_NAME,
                "Key": storage_key,
                "ContentType": req.mime_type,
                "ContentLength": req.file_size,
            },
            ExpiresIn=UPLOAD_URL_EXPIRY,
        )
    except Exception as exc:
        raise _storage_unavailable(exc, operation="init") from exc

    return {
        "recording_id": recording_id,
        "storage_key": storage_key,
        "upload_url": upload_url,
        "required_headers": {
            "Content-Type": req.mime_type,
            "Content-Length": str(req.file_size),
        },
    }


@router.post("/complete", response_model=CompleteResponse)
def complete_recording(
    req: CompleteRequest,
    student: Student = Depends(get_current_student),
):
    """Verify ownership, existence, MIME and canonical audio-size boundaries."""
    expected_prefix = f"audio/{student.id}/"
    if not req.storage_key.startswith(expected_prefix):
        raise HTTPException(status_code=403, detail="Storage key does not belong to this student")

    s3 = _get_s3()
    try:
        head = s3.head_object(Bucket=S3_BUCKET_NAME, Key=req.storage_key)
    except ClientError as exc:
        code = str(exc.response.get("Error", {}).get("Code") or "")
        if code in {"404", "NoSuchKey", "NotFound"}:
            raise HTTPException(status_code=404, detail="Audio object not found in storage") from exc
        raise _storage_unavailable(exc, operation="complete-head") from exc
    except BotoCoreError as exc:
        raise _storage_unavailable(exc, operation="complete-head") from exc

    file_size = int(head.get("ContentLength") or 0)
    mime_type = str(head.get("ContentType") or "")

    try:
        _validate_audio_metadata(file_size=file_size, mime_type=mime_type)
    except HTTPException as validation_error:
        if validation_error.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE:
            try:
                s3.delete_object(Bucket=S3_BUCKET_NAME, Key=req.storage_key)
            except Exception as exc:
                logger.warning(
                    "Failed to remove oversized recording object %s: %s",
                    req.storage_key,
                    type(exc).__name__,
                )
        raise

    return {
        "status": "ok",
        "storage_key": req.storage_key,
        "file_size": file_size,
        "mime_type": mime_type,
    }


@router.get("/stream/{student_id}/{recording_id}", response_model=StreamResponse)
def stream_recording(
    student_id: int,
    recording_id: str,
    researcher=Depends(get_current_researcher),
):
    storage_key = f"audio/{student_id}/{recording_id}.webm"

    s3 = _get_s3()
    try:
        s3.head_object(Bucket=S3_BUCKET_NAME, Key=storage_key)
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": S3_BUCKET_NAME, "Key": storage_key},
            ExpiresIn=STREAM_URL_EXPIRY,
        )
    except ClientError as exc:
        code = str(exc.response.get("Error", {}).get("Code") or "")
        if code in {"404", "NoSuchKey", "NotFound"}:
            raise HTTPException(status_code=404, detail="Recording not found") from exc
        raise _storage_unavailable(exc, operation="stream") from exc
    except BotoCoreError as exc:
        raise _storage_unavailable(exc, operation="stream") from exc

    return {"url": url, "expires_in": STREAM_URL_EXPIRY}


@router.get("/stream-by-key")
def stream_by_key(
    key: str,
    researcher=Depends(get_current_researcher),
):
    if not key.startswith("audio/"):
        raise HTTPException(status_code=400, detail="Invalid recording key")

    s3 = _get_s3()
    try:
        s3.head_object(Bucket=S3_BUCKET_NAME, Key=key)
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": S3_BUCKET_NAME, "Key": key},
            ExpiresIn=STREAM_URL_EXPIRY,
        )
    except ClientError as exc:
        code = str(exc.response.get("Error", {}).get("Code") or "")
        if code in {"404", "NoSuchKey", "NotFound"}:
            raise HTTPException(status_code=404, detail="Recording not found") from exc
        raise _storage_unavailable(exc, operation="stream-by-key") from exc
    except BotoCoreError as exc:
        raise _storage_unavailable(exc, operation="stream-by-key") from exc

    return {"url": url, "expires_in": STREAM_URL_EXPIRY}
