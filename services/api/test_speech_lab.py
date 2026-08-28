import speech_lab
from speech_provider import ProviderResult, ProviderWord


def test_speech_lab_rejects_unauthenticated_client(client):
    response = client.get("/api/admin/speech-lab/targets")
    assert response.status_code == 401
    assert response.json()["detail"] == "يرجى تسجيل الدخول أولًا"


def test_speech_lab_rejects_student_client(student_client):
    response = student_client.get("/api/admin/speech-lab/targets")
    assert response.status_code == 403
    assert response.json()["detail"] == "هذه الصفحة متاحة للمشرف فقط"


def test_speech_lab_targets_come_from_canonical_catalog(researcher_client):
    response = researcher_client.get("/api/admin/speech-lab/targets")
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == len(payload["targets"])
    assert payload["count"] > 0
    assert payload["catalog_version"]

    targets = payload["targets"]
    assert all(target["interaction_type"] in {"read_aloud", "timed_read_aloud"} for target in targets)
    assert all(target["reference_text"].strip() for target in targets)
    assert {target["group"] for target in targets} & {"pretest", "posttest", "level_1", "level_2", "level_3", "reinforcement"}


def test_speech_lab_reports_provider_as_unconfigured_without_credentials(researcher_client, monkeypatch):
    monkeypatch.delenv("HIMMA_ASR_PROVIDER", raising=False)
    monkeypatch.delenv("HIMMA_GOOGLE_CLOUD_PROJECT", raising=False)

    response = researcher_client.get("/api/admin/speech-lab/provider")
    assert response.status_code == 200
    assert response.json()["configured"] is False
    assert response.json()["provider"] is None


def test_speech_lab_analysis_is_reference_guided_and_academically_neutral(researcher_client, monkeypatch):
    captured = {}

    class LabProvider:
        name = "lab-test-provider"

        def transcribe_reference_guided(self, *, audio_bytes, mime_type, reference_text, language="ar-OM"):
            captured.update(
                audio_bytes=audio_bytes,
                mime_type=mime_type,
                reference_text=reference_text,
                language=language,
            )
            return ProviderResult(
                provider_name=self.name,
                model="lab-model-v1",
                transcript="ذهب سامي إلى المدرسة",
                confidence=0.91,
                request_id="lab-request-1",
                words=(ProviderWord(text="ذهب", confidence=0.95),),
                raw_metadata={"test": True},
            )

    monkeypatch.setattr(speech_lab, "build_provider", lambda: LabProvider())

    reference = "ذَهَبَ سَالِمٌ إِلَى الْمَدْرَسَةِ"
    response = researcher_client.post(
        "/api/admin/speech-lab/analyze",
        data={
            "reference_text": reference,
            "target_id": "LAB-TARGET-1",
            "adaptation_mode": "reference",
        },
        files={"audio": ("reading.webm", b"not-real-audio-but-nonempty", "audio/webm")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert captured["reference_text"] == reference
    assert captured["language"] == "ar-OM"
    assert captured["mime_type"] == "audio/webm"
    assert captured["audio_bytes"] == b"not-real-audio-but-nonempty"
    assert payload["lab_only"] is True
    assert payload["academic_effect"] == "none"
    assert payload["pronunciation_status"] == "not_calibrated"
    assert payload["provider"] == "lab-test-provider"
    assert payload["counts"]["substitution"] == 1
    assert payload["counts"]["deletion"] == 0
    assert payload["counts"]["insertion"] == 0
    assert payload["normalized_transcript"] == "ذهب سامي الي المدرسة"


def test_speech_lab_rejects_empty_recording_without_calling_provider(researcher_client, monkeypatch):
    called = False

    def provider_factory():
        nonlocal called
        called = True
        raise AssertionError("provider must not be built for empty audio")

    monkeypatch.setattr(speech_lab, "build_provider", provider_factory)
    response = researcher_client.post(
        "/api/admin/speech-lab/analyze",
        data={"reference_text": "قَلَم", "adaptation_mode": "reference"},
        files={"audio": ("empty.webm", b"", "audio/webm")},
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "ملف التسجيل فارغ"
    assert called is False
