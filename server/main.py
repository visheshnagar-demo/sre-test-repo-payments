"""SRE Payments Test Service FastAPI Application.

Includes comprehensive exception handling, CORS middleware, and safe late-fee calculations.
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

from server.calculator import calculate_late_fee
from server.payments import (
    charge,
    get_payment,
    refund,
    safe_calculate_late_fee,
    process_payment as process_payment_func,
)
from server.models import (
    LateFeeRequest,
    LateFeeResponse,
    PaymentRequest,
    PaymentResponse,
    ChargeRequest,
    RefundRequest,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def _error_loop() -> None:
    """Repeatedly calculate late fee safely in background when APP_ENV=buggy."""
    while True:
        await asyncio.sleep(60)
        try:
            calculate_late_fee(1000.0, 30, 0)
        except Exception as exc:
            logger.exception("Handled exception in background error loop: %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if os.environ.get("APP_ENV") == "buggy":
        logger.warning("APP_ENV=buggy — background error loop active")
        try:
            calculate_late_fee(1000.0, 30, 0)
        except Exception as exc:
            logger.exception("Handled exception in lifespan startup: %s", exc)
        asyncio.create_task(_error_loop())
    yield


app = FastAPI(
    title="SRE Payments Test Service",
    description="BFSI loan payment service with exception handling and retry logic",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Middleware configuration
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception Handlers
@app.exception_handler(ZeroDivisionError)
async def zero_division_exception_handler(request: Request, exc: ZeroDivisionError):
    logger.exception("Trapped ZeroDivisionError on %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Division by zero in calculation; installment_count must be greater than zero."},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning("HTTPException status %d on %s: %s", exc.status_code, request.url.path, exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception trapped on %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred while processing the request."},
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
        result = safe_calculate_late_fee(req.principal, req.overdue_days, req.installment_count)
        return LateFeeResponse(**result)
    except Exception as exc:
        logger.exception("Error processing /calculate-late-fee: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Error calculating late fee",
        )


@app.post("/process-payment", response_model=PaymentResponse)
def process_payment_endpoint(req: PaymentRequest):
    try:
        res = process_payment_func(req.payment_id, req.amount, req.borrower_id)
        return PaymentResponse(
            payment_id=res["payment_id"],
            status=res["status"],
            amount=res["amount"],
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        logger.exception("Error in /process-payment: %s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Payment processing failed")


@app.post("/charge", response_model=PaymentResponse)
def charge_endpoint(req: ChargeRequest):
    try:
        res = charge(req.payment_id, req.amount, req.borrower_id)
        return PaymentResponse(
            payment_id=res["payment_id"],
            status=res["status"],
            amount=res["amount"],
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        logger.exception("Error in /charge: %s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Charge failed")


@app.get("/payments/{payment_id}")
def get_payment_endpoint(payment_id: str):
    res = get_payment(payment_id)
    if not res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    return res


@app.post("/refund")
def refund_endpoint(req: RefundRequest):
    try:
        res = refund(req.payment_id, req.amount)
        return res
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        logger.exception("Error in /refund: %s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Refund failed")
