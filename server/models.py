from pydantic import BaseModel, Field


class LateFeeRequest(BaseModel):
    principal: float = Field(..., gt=0, description="Loan principal amount")
    overdue_days: int = Field(
        ..., ge=0, description="Number of days payment is overdue"
    )
    installment_count: int = Field(..., ge=0, description="Number of installments")


class LateFeeResponse(BaseModel):
    principal: float
    overdue_days: int
    installment_count: int
    daily_rate: float
    late_fee: float


class PaymentRequest(BaseModel):
    payment_id: str
    amount: float = Field(..., gt=0)
    borrower_id: str


class PaymentResponse(BaseModel):
    payment_id: str
    status: str
    amount: float
