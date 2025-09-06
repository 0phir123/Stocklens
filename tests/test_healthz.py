import pytest
from httpx import AsyncClient
from httpx import ASGITransport

from api.main import app


@pytest.mark.asyncio  # type: ignore[misc]
async def test_healthz() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
