"""The native grading router must not orphan students when Azure is disabled.

Direct enqueue_reading tests intentionally bypass this deployment feature
gate to test the engine itself. Only real submission callers apply the gate.
"""
from v2_reading_engine import runtime, submission_bridge


def test_offline_native_runtime_keeps_previous_pending_student_responses(monkeypatch):
    monkeypatch.setattr(runtime, "native_runtime_configuration", lambda: None)
    assert submission_bridge.native_submissions_enabled() is False


def test_enabled_native_runtime_selects_single_engine(monkeypatch):
    configured = object()
    monkeypatch.setattr(runtime, "native_runtime_configuration", lambda: configured)
    assert submission_bridge.native_submissions_enabled() is True
