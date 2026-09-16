import activities
import activities_v4
from activity_runtime import router as activity_router
from main import app


EXPECTED = {
    ("GET", "/activities/status"),
    ("POST", "/activities/start"),
    ("GET", "/activities/session/{session_id}/progress"),
    ("GET", "/activities/session/{session_id}/next"),
    ("POST", "/activities/session/{session_id}/attempt/{item_id}/submit"),
}


def _get_post_routes(routes, *, activities_only: bool = False) -> list[tuple[str, str]]:
    seen: list[tuple[str, str]] = []
    for route in routes:
        path = getattr(route, "path", "")
        if activities_only and not path.startswith("/activities"):
            continue
        for method in getattr(route, "methods", set()) or set():
            if method in {"GET", "POST"}:
                seen.append((method, path))
    return seen


def test_legacy_activity_modules_are_service_only():
    assert not hasattr(activities, "router")
    assert not hasattr(activities_v4, "router")


def test_public_activity_routes_are_unique_and_owned_by_canonical_router():
    seen = _get_post_routes(activity_router.routes)

    for expected in EXPECTED:
        assert seen.count(expected) == 1, f"expected one owner for {expected}, found {seen.count(expected)}"

    assert len(seen) == len(set(seen)), f"duplicate canonical activity routes: {seen}"


def test_application_mounts_each_activity_route_once():
    seen = _get_post_routes(app.routes, activities_only=True)

    for expected in EXPECTED:
        assert seen.count(expected) == 1, f"expected one mounted route for {expected}, found {seen.count(expected)}"

    assert len(seen) == len(set(seen)), f"duplicate mounted activity routes: {seen}"
