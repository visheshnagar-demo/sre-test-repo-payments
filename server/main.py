"""SRE Payments Test Service.

Endpoints:
  GET  /healthz             Liveness probe — always 200
  GET  /readyz              Readiness probe — always 200
  GET  /                    Service info
  POST /calculate-late-fee  Late-fee calculation
  POST /process-payment     Idempotent payment record — always succeeds
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from server.calculator import calculate_late_fee
from server.models import (
    LateFeeRequest,
    LateFeeResponse,
    PaymentRequest,
    PaymentResponse,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def _error_loop() -> None:
    """Periodically run calculation check safely without unhandled exceptions."""
    while True:
        await asyncio.sleep(60)
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
    description="BFSI loan payment service — used for L3 remediation pipeline testing",
    version="1.0.0",
    lifespan=lifespan,
)

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "service": "sre-payments-test",
        "version": "1.0.0",
        "env": os.environ.get("APP_ENV", "clean"),
        "status": "running",
    }


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/readyz")
def readyz():
    return {"status": "ready"}


@app.post("/calculate-late-fee", response_model=LateFeeResponse)
def calculate_late_fee_endpoint(req: LateFeeRequest):
    try:
        result = calculate_late_fee(req.principal, req.overdue_days, req.installment_count)
        return LateFeeResponse(**result)
    except Exception as e:
        logger.exception("Error processing calculate_late_fee_endpoint: %s", e)
        raise HTTPException(status_code=422, detail=str(e))


@app.post("/process-payment", response_model=PaymentResponse)
def process_payment(req: PaymentRequest):
    logger.info("Payment accepted: payment_id=%s amount=%.2f", req.payment_id, req.amount)
    return PaymentResponse(
        payment_id=req.payment_id,
        status="accepted",
        amount=req.amount,
    )
