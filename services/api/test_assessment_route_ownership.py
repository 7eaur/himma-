from assessment_completion import router as completion_router
from assessment_retake import router as retake_router


def _owners(router, path: str, method: str):
    return [route.endpoint.__module__ for route in router.routes if getattr(route, "path", None) == path and method in getattr(route, "methods", set())]


def test_critical_assessment_routes_have_one_owner():
    assert _owners(retake_router, "/assessment/start", "POST") == ["assessment_retake"]
    assert _owners(retake_router, "/assessment/session/{session_id}/finish", "POST") == []
    assert _owners(completion_router, "/assessment/session/{session_id}/finish", "POST") == ["assessment_completion"]
