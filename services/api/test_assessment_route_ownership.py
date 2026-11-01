from assessment import router as assessment_router
from assessment_completion import router as completion_router
from main import app
from assessment_retake import router as retake_router


def _owners(router, path: str, method: str):
    return [route.endpoint.__module__ for route in router.routes if getattr(route, "path", None) == path and method in getattr(route, "methods", set())]


def test_critical_assessment_routes_have_one_owner():
    assert _owners(retake_router, "/assessment/start", "POST") == ["assessment_retake"]
    assert _owners(retake_router, "/assessment/session/{session_id}/finish", "POST") == []
    assert _owners(completion_router, "/assessment/session/{session_id}/finish", "POST") == ["assessment_completion"]


def test_application_assessment_start_has_one_owner():
    # Verify the externally published contract, then the single composition
    # site. Router cloning/route metadata can differ across FastAPI versions;
    # app.openapi() is also exercised by the existing activity ownership tests.
    assert _owners(assessment_router, "/assessment/start", "POST") == []
    assert "post" in app.openapi()["paths"].get("/assessment/start", {})

    import ast
    from pathlib import Path

    tree = ast.parse(Path(__file__).with_name("main.py").read_text(encoding="utf-8"))
    mounts = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "app"
        and node.func.attr == "include_router"
        and len(node.args) == 1
        and isinstance(node.args[0], ast.Name)
        and node.args[0].id == "assessment_retake_router"
    ]
    assert len(mounts) == 1, "assessment_retake_router must be mounted exactly once"
