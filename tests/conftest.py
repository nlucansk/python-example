"""Shared fixtures for the FastAPI boilerplate test suite."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient
from fastapi import FastAPI

from app.middleware import RequestLoggingMiddleware
from app.routes import azure as azure_routes
from app.routes import health, items


def _make_mock_azure():
    azure = MagicMock()
    azure.connect = AsyncMock()
    azure.close = AsyncMock()
    azure.check_keyvault = AsyncMock(return_value=True)
    azure.check_storage = AsyncMock(return_value=True)
    azure.keyvault = None
    azure.blob = None
    return azure


def _build_app(azure_mock) -> FastAPI:
    """Build a fresh FastAPI app with mock Azure clients pre-wired."""
    app = FastAPI()
    app.add_middleware(RequestLoggingMiddleware)
    app.include_router(health.router)
    app.include_router(items.router)
    app.include_router(azure_routes.router)
    app.state.azure = azure_mock
    return app


@pytest.fixture()
def azure_mock():
    return _make_mock_azure()


@pytest.fixture()
def app(azure_mock):
    return _build_app(azure_mock)


@pytest.fixture()
async def client(app: FastAPI):
    """Async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


@pytest.fixture(autouse=True)
def _reset_items_store():
    """Reset the in-memory items store before every test."""
    items._store.clear()
    items._counter = 0
