import recordings


class FakeStreamingBody:
    def __init__(self, payload: bytes):
        self.payload = payload
        self.closed = False

    def iter_chunks(self, chunk_size: int = 64 * 1024):
        for offset in range(0, len(self.payload), chunk_size):
            yield self.payload[offset:offset + chunk_size]

    def close(self):
        self.closed = True


class FakeS3:
    def __init__(self, payload: bytes = b"0123456789"):
        self.payload = payload
        self.calls: list[dict] = []
        self.bodies: list[FakeStreamingBody] = []

    def get_object(self, **kwargs):
        self.calls.append(kwargs)
        range_header = kwargs.get("Range")
        if range_header == "bytes=2-5":
            payload = self.payload[2:6]
            body = FakeStreamingBody(payload)
            self.bodies.append(body)
            return {
                "Body": body,
                "ContentLength": len(payload),
                "ContentType": "audio/webm",
                "ContentRange": f"bytes 2-5/{len(self.payload)}",
            }

        body = FakeStreamingBody(self.payload)
        self.bodies.append(body)
        return {
            "Body": body,
            "ContentLength": len(self.payload),
            "ContentType": "audio/webm",
        }


def test_researcher_audio_playback_streams_private_object_same_origin(researcher_client, monkeypatch):
    s3 = FakeS3()
    monkeypatch.setattr(recordings, "_get_s3", lambda: s3)

    response = researcher_client.get("/recordings/play-by-key?key=audio/7/example.webm")

    assert response.status_code == 200
    assert response.content == b"0123456789"
    assert response.headers["content-type"].startswith("audio/webm")
    assert response.headers["accept-ranges"] == "bytes"
    assert response.headers["cache-control"] == "private, no-store"
    assert response.headers["content-disposition"] == "inline"
    assert s3.calls == [{"Bucket": recordings.S3_BUCKET_NAME, "Key": "audio/7/example.webm"}]
    assert s3.bodies[0].closed is True


def test_researcher_audio_playback_forwards_range_for_native_audio_controls(researcher_client, monkeypatch):
    s3 = FakeS3()
    monkeypatch.setattr(recordings, "_get_s3", lambda: s3)

    response = researcher_client.get(
        "/recordings/play-by-key?key=audio/7/example.webm",
        headers={"Range": "bytes=2-5"},
    )

    assert response.status_code == 206
    assert response.content == b"2345"
    assert response.headers["content-range"] == "bytes 2-5/10"
    assert response.headers["content-length"] == "4"
    assert response.headers["accept-ranges"] == "bytes"
    assert s3.calls == [{
        "Bucket": recordings.S3_BUCKET_NAME,
        "Key": "audio/7/example.webm",
        "Range": "bytes=2-5",
    }]
    assert s3.bodies[0].closed is True


def test_researcher_audio_playback_rejects_invalid_storage_key(researcher_client, monkeypatch):
    s3 = FakeS3()
    monkeypatch.setattr(recordings, "_get_s3", lambda: s3)

    response = researcher_client.get("/recordings/play-by-key?key=not-audio/example.webm")

    assert response.status_code == 400
    assert s3.calls == []


def test_researcher_audio_playback_rejects_invalid_range_before_storage(researcher_client, monkeypatch):
    s3 = FakeS3()
    monkeypatch.setattr(recordings, "_get_s3", lambda: s3)

    response = researcher_client.get(
        "/recordings/play-by-key?key=audio/7/example.webm",
        headers={"Range": "bytes=0-1,4-5"},
    )

    assert response.status_code == 416
    assert s3.calls == []
