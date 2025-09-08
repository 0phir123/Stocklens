# File: api/routers/agent.py
from __future__ import annotations
from typing import Protocol, Dict
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from shared.di import get_metrics_service

router = APIRouter(prefix="/v1/agent", tags=["agent"])


# ---------- DTOs ----------
class AskRequestDTO(BaseModel):
    q: str = Field(..., min_length=1, description="User question")


class AskResponseDTO(BaseModel):
    answer: str
    tool: str


# ---------- Command Protocol ----------
class ToolCommand(Protocol):
    name: str

    def execute(self, q: str) -> str: ...


# ---------- Tools ----------
class EchoTool:
    name = "echo"

    def execute(self, q: str) -> str:
        return f"You said: {q}"


class PricesTool:
    name = "prices"

    def __init__(self) -> None:
        # inject DI service here
        self._svc = get_metrics_service()

    def execute(self, q: str) -> str:
        parts = q.split()
        ticker = parts[-1] if parts else "SPY"
        try:
            series = self._svc.get_prices(symbol=ticker, freq="D")
        except ValueError as e:
            return f"Error: {e}"

        if not series:
            return f"No data for {ticker}."
        last = series[-1]
        return f"Latest adjusted close for {ticker}: {last.value} on {last.when}"


# ---------- Registry ----------
class ToolRegistry:
    def __init__(self) -> None:
        self._tools: Dict[str, ToolCommand] = {}

    def register(self, tool: ToolCommand) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolCommand:
        if name not in self._tools:
            raise KeyError(name)
        return self._tools[name]


registry = ToolRegistry()
registry.register(EchoTool())
registry.register(PricesTool())  # DI inside constructor


# ---------- Route ----------
@router.get("/ask", response_model=AskResponseDTO)  # type: ignore[misc]
def ask(q: str = Query(..., min_length=1), tool: str = Query("echo")) -> AskResponseDTO:
    try:
        cmd = registry.get(tool)
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Unknown tool: {tool}")
    return AskResponseDTO(answer=cmd.execute(q), tool=tool)
