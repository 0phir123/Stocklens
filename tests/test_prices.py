#  File: /tests/test_prices.py
import pytest
from httpx import AsyncClient, ASGITransport
from api.main import app


@pytest.mark.asyncio  # type: ignore[misc]
async def test_prices_happy_path() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/v1/fetch_data/prices", params={"symbol": "SPY", "freq": "D"})
    assert r.status_code == 200
    body = r.json()
    assert body["symbol"] == "SPY"
    assert isinstance(body["points"], list)
    assert len(body["points"]) >= 1
    assert set(body["points"][0].keys()) == {"when", "value"}


@pytest.mark.asyncio  # type: ignore[misc]
async def test_prices_invalid_freq_422() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/v1/fetch_data/prices", params={"symbol": "SPY", "freq": "X"})
    assert r.status_code == 422
