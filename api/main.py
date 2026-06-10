"""
SentinelFlow - FastAPI Application
REST API layer that exposes pipeline results
to the dashboard and external consumers.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import quality, anomalies, drift, metadata
from config.logging_config import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title="SentinelFlow API",
    description="AI-Powered Data Observability Platform API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(quality.router, prefix="/quality", tags=["Data Quality"])
app.include_router(anomalies.router, prefix="/anomalies", tags=["Anomalies"])
app.include_router(drift.router, prefix="/drift", tags=["Drift"])
app.include_router(metadata.router, prefix="/metadata", tags=["Metadata"])


@app.get("/")
def root():
    return {
        "platform": "SentinelFlow",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
def health():
    return {"status": "healthy"}