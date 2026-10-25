"""P08: a retry upload key is single-use across MIME suffixes, not just bytes."""
from io import BytesIO

import pytest
from botocore.exceptions import ClientError
from fastapi import UploadFile
from starlette.datastructures import Headers

import storage


class _FakePrivateObjects:
    def __init__(self):
        self.objects = {}

    def head_object(self, *, Bucket, Key):
        if Key not in self.objects:
            raise ClientError({"Error": {"Code": "404", "Message": "Not Found"}}, "HeadObject")
        return self.objects[Key]

    def put_object(self, *, Bucket, Key, Body, ContentType, Metadata):
        self.objects[Key] = {
            "ContentLength": len(Body), "ContentType": ContentType,
            "Metadata": Metadata.copy(),
        }


def _file(payload: bytes, mime: str) -> UploadFile:
    return UploadFile(
        file=BytesIO(payload),
        filename="synthetic-p08-audio",
        headers=Headers({"content-type": mime}),
    )


@pytest.mark.parametrize("original_mime,changed_mime", [
    ("audio/webm", "audio/mp4"),
    ("audio/mp4", "audio/webm"),
])
def test_idempotency_key_cannot_change_audio_mime_suffix(
    monkeypatch, original_mime, changed_mime,
):
    store = _FakePrivateObjects()
    monkeypatch.setattr(storage, "s3_client", store)
    operation = "p08-test-task-5:stable-upload-key"
    first = storage.upload_audio(_file(b"synthetic-audio-1", original_mime), 12, operation)
    assert first[1] == len(b"synthetic-audio-1")
    assert storage.upload_audio(_file(b"synthetic-audio-1", original_mime), 12, operation) == first

    with pytest.raises(ValueError, match="Idempotency-Key"):
        storage.upload_audio(_file(b"synthetic-audio-2", changed_mime), 12, operation)
    with pytest.raises(ValueError, match="Idempotency-Key"):
        storage.upload_audio(_file(b"synthetic-audio-2", original_mime), 12, operation)
    assert len(store.objects) == 1


def test_new_upload_operation_may_choose_different_format(monkeypatch):
    store = _FakePrivateObjects()
    monkeypatch.setattr(storage, "s3_client", store)
    webm = storage.upload_audio(_file(b"webm-synthetic", "audio/webm"), 12, "task:5:attempt-A")
    mp4 = storage.upload_audio(_file(b"mp4-synthetic", "audio/mp4"), 12, "task:5:attempt-B")
    assert webm[0] != mp4[0]
    assert len(store.objects) == 2
