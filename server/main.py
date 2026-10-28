import asyncio
from contextlib import asynccontextmanager
import logging
import os
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from starlette.middleware.cors import CORSMiddleware

from server.calculator import calculate_late_fee
from server.models import (
    LateFeeRequest,
    LateFeeResponse,
    PaymentRequest,
    PaymentResponse,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("payments-service")


async def _error_loop():
    """Background loop that simulates occasional calculations and logs appropriately."""
    while True:
        await asyncio.sleep(5)
        try:
            calculate_late_fee(1000.0, 30, 0)
        except Exception:
            logger.exception("Error in background calculate_late_fee loop")


@asynccontextmanager
async def lifespan(app: FastAPI):
    if os.environ.get("APP_ENV") == "buggy":
        logger.warning("APP_ENV=buggy — running calculate_late_fee background loop")
        try:
            calculate_late_fee(1000.0, 30, 0)
        except Exception:
            logger.exception("Error during startup calculate_late_fee execution")
        asyncio.create_task(_error_loop())
    yield


app = FastAPI(
    title="SRE Payments Test Service",
    description="Service for SRE incident simulation and late fee calculations",
    version="1.0.0",
    lifespan=lifespan,
)

ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000"
).split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=Dict[str, Any])
def root():
    return {
        "service": "sre-payments-test",
        "status": "running",
        "version": "1.0.0",
    }


@app.get("/healthz", response_model=Dict[str, str])
def healthz():
    return {"status": "ok"}


@app.get("/readyz", response_model=Dict[str, str])
def readyz():
    return {"status": "ready"}


@app.get("/metrics", response_model=Dict[str, Any])
def metrics():
    return {
        "service": "sre-payments-test",
        "status": "healthy",
        "metrics": {
            "uptime_status": "ok",
            "active": True,
        },
    }


@app.post("/calculate-late-fee", response_model=LateFeeResponse)
def calculate_late_fee_endpoint(req: LateFeeRequest):
    logger.info(
        "Received calculate-late-fee request: principal=%.2f, overdue_days=%d, installment_count=%d",
        req.principal,
        req.overdue_days,
        req.installment_count,
    )
    try:
        result = calculate_late_fee(
            req.principal, req.overdue_days, req.installment_count
        )
        logger.info(
            "Calculated late fee successfully: principal=%.2f, late_fee=%.2f",
            req.principal,
            result.get("late_fee", 0.0),
        )
        return LateFeeResponse(**result)
    except Exception as e:
        logger.exception("Error processing calculate_late_fee_endpoint: %s", e)
        raise HTTPException(status_code=422, detail=str(e))


@app.post("/process-payment", response_model=PaymentResponse)
def process_payment(req: PaymentRequest):
    logger.info(
        "Payment accepted: payment_id=%s amount=%.2f", req.payment_id, req.amount
    )
    return PaymentResponse(
        payment_id=req.payment_id,
        status="accepted",
        amount=req.amount,
    )
