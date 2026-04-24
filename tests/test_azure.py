"""Tests for /api/azure Key Vault and Storage Account endpoints."""

from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.mark.asyncio
async def test_keyvault_secrets_not_configured(client):
    """Returns 404 when Key Vault client is not configured."""
    resp = await client.get("/api/azure/keyvault/secrets")
    assert resp.status_code == 404
    assert "not configured" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_keyvault_list_secrets(client, app):
    """Lists secret names when Key Vault is configured."""
    mock_prop = MagicMock()
    mock_prop.name = "my-secret"
    mock_prop.id = "https://vault.azure.net/secrets/my-secret"

    async def mock_list():
        yield mock_prop

    mock_kv = MagicMock()
    mock_kv.list_properties_of_secrets = mock_list
    app.state.azure.keyvault = mock_kv

    resp = await client.get("/api/azure/keyvault/secrets")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["name"] == "my-secret"


@pytest.mark.asyncio
async def test_keyvault_get_secret(client, app):
    """Retrieves a specific secret value."""
    mock_secret = MagicMock()
    mock_secret.name = "db-password"
    mock_secret.value = "s3cret"

    mock_kv = MagicMock()
    mock_kv.get_secret = AsyncMock(return_value=mock_secret)
    app.state.azure.keyvault = mock_kv

    resp = await client.get("/api/azure/keyvault/secrets/db-password")
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "db-password"
    assert body["value"] == "s3cret"


@pytest.mark.asyncio
async def test_keyvault_get_secret_not_found(client, app):
    """Returns 404 when secret does not exist."""
    mock_kv = MagicMock()
    mock_kv.get_secret = AsyncMock(side_effect=Exception("SecretNotFound"))
    app.state.azure.keyvault = mock_kv

    resp = await client.get("/api/azure/keyvault/secrets/nonexistent")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_storage_containers_not_configured(client):
    """Returns 404 when Storage client is not configured."""
    resp = await client.get("/api/azure/storage/containers")
    assert resp.status_code == 404
    assert "not configured" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_storage_list_containers(client, app):
    """Lists containers when Storage is configured."""
    mock_container = MagicMock()
    mock_container.name = "my-container"

    async def mock_list():
        yield mock_container

    mock_blob = MagicMock()
    mock_blob.list_containers = mock_list
    app.state.azure.blob = mock_blob

    resp = await client.get("/api/azure/storage/containers")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["name"] == "my-container"


@pytest.mark.asyncio
async def test_storage_list_blobs(client, app):
    """Lists blobs in a container."""
    mock_blob_item = MagicMock()
    mock_blob_item.name = "file.txt"
    mock_blob_item.size = 1024
    mock_blob_item.content_settings = MagicMock()
    mock_blob_item.content_settings.content_type = "text/plain"

    async def mock_list():
        yield mock_blob_item

    mock_container_client = MagicMock()
    mock_container_client.list_blobs = mock_list

    mock_blob_svc = MagicMock()
    mock_blob_svc.get_container_client = MagicMock(return_value=mock_container_client)
    app.state.azure.blob = mock_blob_svc

    resp = await client.get("/api/azure/storage/containers/my-container/blobs")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["name"] == "file.txt"
    assert body[0]["size"] == 1024
    assert body[0]["content_type"] == "text/plain"


@pytest.mark.asyncio
async def test_storage_list_blobs_container_not_found(client, app):
    """Returns 404 when container does not exist."""

    async def mock_list():
        raise Exception("ContainerNotFound")
        yield  # noqa: unreachable - makes this an async generator

    mock_container_client = MagicMock()
    mock_container_client.list_blobs = mock_list

    mock_blob_svc = MagicMock()
    mock_blob_svc.get_container_client = MagicMock(return_value=mock_container_client)
    app.state.azure.blob = mock_blob_svc

    resp = await client.get("/api/azure/storage/containers/nonexistent/blobs")
    assert resp.status_code == 404
