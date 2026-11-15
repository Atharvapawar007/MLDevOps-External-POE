"""
app.py - FastAPI application wrapping the addition logic with production-ready endpoints.

Includes:
- Health check endpoint (/health)
- POST /api/v1/add for JSON payloads
- GET /api/v1/add for query parameters
- POST /api/v1/add/batch for batch calculation and logging for Evidently drift monitoring
- OpenAPI / Swagger documentation at /docs
"""

import os
import sys
import csv
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Optional

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field

try:
    from src.addition import add_numbers
except ImportError:
    from addition import add_numbers

# Configuration
DATA_LOG_PATH = os.getenv("DATA_LOG_PATH", "data/current_data.csv")

app = FastAPI(
    title="Addition MLOps Service",
    description="FastAPI service for arithmetic addition integrated with Pytest, Evidently, and Jenkins CI/CD.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)


# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------

class AdditionRequest(BaseModel):
    num1: float = Field(..., description="First number to add", example=15.5)
    num2: float = Field(..., description="Second number to add", example=24.5)

    model_config = {
        "json_schema_extra": {
            "example": {
                "num1": 15.5,
                "num2": 24.5
            }
        }
    }


class AdditionResponse(BaseModel):
    num1: float
    num2: float
    operation: str = "addition"
    result: float
    timestamp: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "num1": 15.5,
                "num2": 24.5,
                "operation": "addition",
                "result": 40.0,
                "timestamp": "2026-11-15T04:30:00Z"
            }
        }
    }


class BatchAdditionRequest(BaseModel):
    items: List[AdditionRequest]


class BatchAdditionResponse(BaseModel):
    count: int
    results: List[AdditionResponse]


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: str


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def log_prediction(num1: float, num2: float, result: float, filepath: str = DATA_LOG_PATH) -> None:
    """Log prediction data to CSV for Evidently drift and quality monitoring."""
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        file_exists = os.path.isfile(filepath)
        with open(filepath, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["num1", "num2", "result", "timestamp"])
            writer.writerow([num1, num2, result, datetime.now(timezone.utc).isoformat()])
    except Exception as e:
        # Avoid breaking the request if logging encounters a filesystem error
        print(f"[Warning] Failed to log request data for monitoring: {e}")


# ---------------------------------------------------------------------------
# API Routes
# ---------------------------------------------------------------------------

@app.get("/", tags=["General"])
def root():
    """Root welcoming endpoint with links to documentation and health check."""
    return {
        "message": "Welcome to Addition MLOps Service API",
        "documentation": "/docs",
        "health": "/health",
        "endpoints": {
            "POST_add": "/api/v1/add",
            "GET_add": "/api/v1/add?num1=10&num2=20",
            "POST_batch_add": "/api/v1/add/batch"
        }
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    """Health check endpoint used by Jenkins and container orchestrators."""
    return HealthResponse(
        status="healthy",
        service="Addition MLOps API",
        version="1.0.0",
        timestamp=datetime.now(timezone.utc).isoformat()
    )


@app.post("/api/v1/add", response_model=AdditionResponse, status_code=status.HTTP_200_OK, tags=["Operations"])
def add_via_post(payload: AdditionRequest, log_data: bool = Query(True, description="Log to CSV for Evidently monitoring")):
    """
    Accept two numbers in JSON body and return their addition.
    """
    try:
        result = add_numbers(payload.num1, payload.num2)
        ts = datetime.now(timezone.utc).isoformat()

        if log_data:
            log_prediction(payload.num1, payload.num2, result)

        return AdditionResponse(
            num1=payload.num1,
            num2=payload.num2,
            operation="addition",
            result=result,
            timestamp=ts
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error computing addition: {str(exc)}"
        )


@app.get("/api/v1/add", response_model=AdditionResponse, status_code=status.HTTP_200_OK, tags=["Operations"])
def add_via_get(
    num1: float = Query(..., description="First number"),
    num2: float = Query(..., description="Second number"),
    log_data: bool = Query(True, description="Log to CSV for Evidently monitoring")
):
    """
    Accept two numbers as URL query parameters and return their addition.
    """
    try:
        result = add_numbers(num1, num2)
        ts = datetime.now(timezone.utc).isoformat()

        if log_data:
            log_prediction(num1, num2, result)

        return AdditionResponse(
            num1=num1,
            num2=num2,
            operation="addition",
            result=result,
            timestamp=ts
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error computing addition: {str(exc)}"
        )


@app.post("/api/v1/add/batch", response_model=BatchAdditionResponse, status_code=status.HTTP_200_OK, tags=["Operations"])
def add_batch(payload: BatchAdditionRequest, log_data: bool = Query(True, description="Log batch to CSV for Evidently monitoring")):
    """
    Process multiple addition requests in a single batch.
    """
    results: List[AdditionResponse] = []
    ts = datetime.now(timezone.utc).isoformat()

    for item in payload.items:
        res = add_numbers(item.num1, item.num2)
        if log_data:
            log_prediction(item.num1, item.num2, res)
        results.append(
            AdditionResponse(
                num1=item.num1,
                num2=item.num2,
                operation="addition",
                result=res,
                timestamp=ts
            )
        )

    return BatchAdditionResponse(
        count=len(results),
        results=results
    )
