# File: /tests/test_agent_echo.py
import pytest
from httpx import AsyncClient, ASGITransport
from api.main import app


@pytest.mark.asyncio  # type: ignore[misc]
async def test_agent_echo_default_tool() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/v1/agent/ask", params={"q": "hello world"})
    assert r.status_code == 200
    data = r.json()
    assert data["tool"] == "echo"
    assert "You said: hello world" in data["answer"]


@pytest.mark.asyncio  # type: ignore[misc]
async def test_agent_unknown_tool_400() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/v1/agent/ask", params={"q": "hi", "tool": "nope"})
    assert r.status_code == 400
    assert "Unknown tool" in r.text
