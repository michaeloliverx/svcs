from __future__ import annotations

from collections.abc import Callable
from typing import Any

from flask import Flask, current_app, g, has_app_context

from ._core import Container, Registry, ServicePing


def init_app(app: Flask, registry: Registry | None = None) -> Flask:
    if registry is None:
        registry = Registry()

    app.config["svc_registry"] = registry
    app.teardown_appcontext(teardown)

    return app


def get(svc_type: type) -> Any:
    """
    Get registered service of *svc_type*.

    Return Any until https://github.com/python/mypy/issues/4717 is fixed.
    """
    _, container = _ensure_req_data()

    return container.get(svc_type)


def register_factory(
    svc_type: type,
    factory: Callable,
    *,
    cleanup: Callable | None = None,
    ping: Callable | None = None,
) -> None:
    registry, container = _ensure_req_data()

    container.forget_service_type(svc_type)
    registry.register_factory(svc_type, factory, cleanup=cleanup, ping=ping)


def register_value(
    svc_type: type,
    instance: object,
    *,
    cleanup: Callable | None = None,
    ping: Callable | None = None,
) -> None:
    registry, container = _ensure_req_data()

    container.forget_service_type(svc_type)
    registry.register_value(svc_type, instance, cleanup=cleanup, ping=ping)


def get_pings() -> list[ServicePing]:
    _, container = _ensure_req_data()

    return container.get_pings()


def teardown(exc: BaseException | None) -> None:
    """
    To be used with Flask.teardown_appcontext that requires to take an
    exception.

    The app context is torn down after the response is sent.
    """
    if has_app_context():
        close()


def close() -> None:
    """
    Remove container & run all registered cleanups.
    """
    if container := g.pop("svc_container", None):
        container.close()


def _ensure_req_data() -> tuple[Registry, Container]:
    registry: Registry = current_app.config["svc_registry"]
    if "svc_container" not in g:
        g.svc_container = Container(registry)

    return registry, g.svc_container
