# RF: RNF001 — health check endpoint
"""Integration tests for the health-check endpoint."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint_ok(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_api_v1_health_returns_sprint(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["sprint"] == 2
    assert "version" in data
    assert "environment" in data


@pytest.mark.asyncio
async def test_api_docs_available(client: AsyncClient) -> None:
    response = await client.get("/api/docs")
    assert response.status_code == 200
