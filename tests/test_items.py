"""Tests for /api/items CRUD endpoints."""

import pytest


@pytest.mark.asyncio
async def test_create_item(client):
    resp = await client.post("/api/items", json={"name": "Widget", "description": "A fine widget"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Widget"
    assert body["description"] == "A fine widget"
    assert "id" in body


@pytest.mark.asyncio
async def test_list_items(client):
    # empty at first
    resp = await client.get("/api/items")
    assert resp.status_code == 200
    assert resp.json() == []

    # create two items, then list
    await client.post("/api/items", json={"name": "A"})
    await client.post("/api/items", json={"name": "B"})

    resp = await client.get("/api/items")
    assert resp.status_code == 200
    names = {item["name"] for item in resp.json()}
    assert names == {"A", "B"}


@pytest.mark.asyncio
async def test_get_item(client):
    create_resp = await client.post("/api/items", json={"name": "Gizmo", "description": "Neat"})
    item_id = create_resp.json()["id"]

    resp = await client.get(f"/api/items/{item_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == item_id
    assert body["name"] == "Gizmo"
    assert body["description"] == "Neat"


@pytest.mark.asyncio
async def test_get_item_not_found(client):
    resp = await client.get("/api/items/9999")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Item not found"


@pytest.mark.asyncio
async def test_delete_item(client):
    create_resp = await client.post("/api/items", json={"name": "Ephemeral"})
    item_id = create_resp.json()["id"]

    resp = await client.delete(f"/api/items/{item_id}")
    assert resp.status_code == 204

    # confirm it is gone
    resp = await client.get(f"/api/items/{item_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_item_not_found(client):
    resp = await client.delete("/api/items/9999")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Item not found"
