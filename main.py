from __future__ import annotations

from fastapi import FastAPI

from apps.src.controllers.routing import router as analysis_router


app = FastAPI(
    title="Cluster Analyzer Service",
    version="0.1.0",
    description="Cluster-aware analyzer service with LangChain and LangGraph integration.",
)

app.include_router(analysis_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "cluster-analyzer"}
