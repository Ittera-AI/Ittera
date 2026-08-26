"""API composition-root liveness and dependency-readiness checks."""

import main


def test_liveness_endpoints_do_not_touch_dependencies(client, monkeypatch) -> None:
    monkeypatch.setattr(
        main,
        "_check_database",
        lambda: (_ for _ in ()).throw(AssertionError("database check called")),
    )
    monkeypatch.setattr(
        main,
        "_check_broker",
        lambda: (_ for _ in ()).throw(AssertionError("broker check called")),
    )

    for path in ("/health", "/health/live"):
        response = client.get(path)
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "service": "iterra-api"}


def test_readiness_reports_healthy_dependencies(client, monkeypatch) -> None:
    monkeypatch.setattr(main, "_check_database", lambda: True)
    monkeypatch.setattr(main, "_check_broker", lambda: True)

    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "service": "iterra-api",
        "checks": {"database": "ok", "broker": "ok"},
    }


def test_readiness_fails_closed_with_typed_dependency_state(
    client,
    monkeypatch,
) -> None:
    monkeypatch.setattr(main, "_check_database", lambda: False)
    monkeypatch.setattr(main, "_check_broker", lambda: True)

    response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "service": "iterra-api",
        "checks": {"database": "unavailable", "broker": "ok"},
    }
