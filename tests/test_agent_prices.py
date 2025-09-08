# File: /tests/test_agent_prices.py
import pytest
from httpx import AsyncClient, ASGITransport
from api.main import app


@pytest.mark.asyncio  # type: ignore[misc]
async def test_agent_prices_tool_happy_path() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/v1/agent/ask", params={"q": "price SPY", "tool": "prices"})
    assert r.status_code == 200
    data = r.json()
    assert data["tool"] == "prices"
    assert "Latest adjusted close for SPY:" in data["answer"]
