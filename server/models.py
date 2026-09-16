"""Pydantic models for SRE Payments Service."""

from typing import Optional
from pydantic import BaseModel, Field


class LateFeeRequest(BaseModel):
    principal: float = Field(..., description="Principal amount of the loan")
    overdue_days: int = Field(..., description="Number of overdue days")
    installment_count: int = Field(..., description="Number of installments")


class LateFeeResponse(BaseModel):
    late_fee: float
    daily_rate: float


class PaymentRequest(BaseModel):
    payment_id: str
    amount: float
    borrower_id: str


class PaymentResponse(BaseModel):
    payment_id: str
    status: str
    amount: float


class ChargeRequest(BaseModel):
    payment_id: str
    amount: float
    borrower_id: str


class RefundRequest(BaseModel):
    payment_id: str
    amount: Optional[float] = None
