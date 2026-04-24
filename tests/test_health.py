"""Tests for /healthz (liveness) and /readyz (readiness) endpoints."""

import pytest


@pytest.mark.asyncio
async def test_liveness(client):
    resp = await client.get("/healthz")
    assert resp.status_code == 200
    body = resp.json()
    assert body == {"status": "alive"}


@pytest.mark.asyncio
async def test_readiness_all_ok(client, app):
    """Both keyvault and storage checks pass -> 200."""
    resp = await client.get("/readyz")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ready"
    assert body["checks"]["keyvault"] is True
    assert body["checks"]["storage"] is True


@pytest.mark.asyncio
async def test_readiness_keyvault_down(client, app):
    """Keyvault check fails -> 503."""
    app.state.azure.check_keyvault.return_value = False

    resp = await client.get("/readyz")
    assert resp.status_code == 503
    body = resp.json()
    assert body["status"] == "not_ready"
    assert body["checks"]["keyvault"] is False
    assert body["checks"]["storage"] is True


@pytest.mark.asyncio
async def test_readiness_storage_down(client, app):
    """Storage check fails -> 503."""
    app.state.azure.check_storage.return_value = False

    resp = await client.get("/readyz")
    assert resp.status_code == 503
    body = resp.json()
    assert body["status"] == "not_ready"
    assert body["checks"]["keyvault"] is True
    assert body["checks"]["storage"] is False
