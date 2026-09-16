import ast
from pathlib import Path

import activities
import activities_v4
from activity_runtime import router as activity_router
from main import app


EXPECTED = {
    ("GET", "/activities/status"),
    ("POST", "/activities/start"),
    ("GET", "/activities/session/{session_id}/progress"),
    ("GET", "/activities/session/{session_id}/rerecord-tasks"),
    ("POST", "/activities/session/{session_id}/attempt/{item_id}/step/{step_id}/rerecord/start"),
    ("GET", "/activities/session/{session_id}/next"),
    ("POST", "/activities/session/{session_id}/attempt/{item_id}/submit"),
}


def _get_post_routes(routes) -> list[tuple[str, str]]:
    seen: list[tuple[str, str]] = []
    for route in routes:
        path = getattr(route, "path", "")
        for method in getattr(route, "methods", set()) or set():
            if method in {"GET", "POST"}:
                seen.append((method, path))
    return seen


def test_legacy_activity_modules_are_service_only():
    assert not hasattr(activities, "router")
    assert not hasattr(activities_v4, "router")


def test_public_activity_routes_are_unique_and_owned_by_canonical_router():
    seen = _get_post_routes(activity_router.routes)
    activity_seen = [entry for entry in seen if entry[1].startswith("/activities")]

    assert set(activity_seen) == EXPECTED
    assert len(activity_seen) == len(set(activity_seen)), f"duplicate canonical activity routes: {activity_seen}"

    for route in activity_router.routes:
        if not getattr(route, "path", "").startswith("/activities"):
            continue
        endpoint = getattr(route, "endpoint", None)
        module = getattr(endpoint, "__module__", "")
        assert module.rsplit(".", 1)[-1] == "activity_runtime"


def test_application_wires_only_the_canonical_activity_router_once():
    """Prove router ownership at the composition boundary without relying on
    FastAPI's cloned APIRoute objects, which are an implementation detail.
    """
    tree = ast.parse(Path(__file__).with_name("main.py").read_text(encoding="utf-8"))

    canonical_imports = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module == "activity_runtime"
        and any(alias.name == "router" and alias.asname == "activities_router" for alias in node.names)
    ]
    assert len(canonical_imports) == 1

    forbidden_router_imports = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module in {"activities", "activities_v4"}
        and any(alias.name == "router" for alias in node.names)
    ]
    assert forbidden_router_imports == []

    mounts = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "app"
        and node.func.attr == "include_router"
        and node.args
        and isinstance(node.args[0], ast.Name)
        and node.args[0].id == "activities_router"
    ]
    assert len(mounts) == 1


def test_openapi_exposes_exact_canonical_activity_contract():
    paths = app.openapi()["paths"]
    exposed = {
        (method.upper(), path)
        for path, operations in paths.items()
        if path.startswith("/activities")
        for method in operations
        if method.upper() in {"GET", "POST"}
    }
    assert exposed == EXPECTED
