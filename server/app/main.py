"""ASGI entry point; domain routers are assembled in ``app.api.application``."""

from app.api.application import app, manager

__all__ = ["app", "manager"]
