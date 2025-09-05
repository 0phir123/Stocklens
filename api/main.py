# File: api/main.py    
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from shared.config import settings
from shared.logging import setup_logging
from api.routers.insights import router as insights_router




def create_app() -> FastAPI:
    setup_logging(settings.log_level)
    app = FastAPI(title="StockLens API", version="0.1.0",
                  default_response_class=ORJSONResponse)
    app.include_router(insights_router)
    return app


app = create_app()



@app.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok"}
@app.get("/v1/agent/ask")
async def agent_ask(q: str) -> dict:
    return {"answer": f"(stub) you asked: {q}"}