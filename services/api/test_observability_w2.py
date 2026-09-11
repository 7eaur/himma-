"""A10/W2 operational-observability regression coverage."""

import json
import logging

from observability import logger as ops_logger


def test_request_id_is_returned_and_invalid_external_id_is_not_reflected(client):
    valid = client.get("/health", headers={"x-request-id": "trace-12345678"})
    assert valid.status_code == 200
    assert valid.headers["x-request-id"] == "trace-12345678"

    invalid = client.get("/health", headers={"x-request-id": "bad id with spaces"})
    assert invalid.status_code == 200
    generated = invalid.headers["x-request-id"]
    assert generated != "bad id with spaces"
    assert len(generated) >= 8


def test_failed_student_auth_signal_is_structured_and_does_not_log_raw_code(client, caplog):
    raw_code = "999998"
    with caplog.at_level(logging.INFO, logger=ops_logger.name):
        response = client.post(
            "/auth/student-login",
            json={"access_code": raw_code},
            headers={"x-request-id": "authtrace-123456"},
        )

    assert response.status_code == 401
    messages = [record.getMessage() for record in caplog.records if "auth_security_signal" in record.getMessage()]
    assert messages
    assert raw_code not in "\n".join(messages)
    event = json.loads(messages[-1])
    assert event["event"] == "auth_security_signal"
    assert event["request_id"] == "authtrace-123456"
    assert event["scope"] == "student-login"
    assert event["outcome"] == "invalid_credentials"
    assert len(event["identifier_hash"]) == 64
    assert len(event["client_hash"]) == 64
