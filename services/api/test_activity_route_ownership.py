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


def test_application_mounts_every_canonical_activity_endpoint_once():
    canonical_routes = [
        route
        for route in activity_router.routes
        if getattr(route, "path", "").startswith("/activities")
    ]
    mounted_routes = list(app.routes)

    for canonical in canonical_routes:
        canonical_methods = {
            method for method in (getattr(canonical, "methods", set()) or set())
            if method in {"GET", "POST"}
        }
        matches = [
            mounted
            for mounted in mounted_routes
            if getattr(mounted, "endpoint", None) is getattr(canonical, "endpoint", None)
            and canonical_methods.issubset(getattr(mounted, "methods", set()) or set())
        ]
        assert len(matches) == 1, (
            f"expected one mounted owner for {canonical_methods} {canonical.path}; "
            f"found {len(matches)}"
        )


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
