"""Payment operations module with exception handling, input validation, and retry logic."""

import logging
from typing import Dict, Any, Optional

from server.calculator import calculate_late_fee, retry_on_exception

logger = logging.getLogger(__name__)

# In-memory storage for payments (for demonstration / testing)
_PAYMENTS_DB: Dict[str, Dict[str, Any]] = {}


def safe_calculate_late_fee(principal: float, overdue_days: int, installment_count: int) -> Dict[str, float]:
    """Safely calculate late fee without allowing ZeroDivisionError to escape."""
    try:
        return calculate_late_fee(principal, overdue_days, installment_count)
    except ZeroDivisionError as exc:
        logger.error("ZeroDivisionError trapped in safe_calculate_late_fee: %s", exc)
        return {"late_fee": 0.0, "daily_rate": 0.18 / 365.0}
    except Exception as exc:
        logger.error("Unhandled exception trapped in safe_calculate_late_fee: %s", exc)
        return {"late_fee": 0.0, "daily_rate": 0.18 / 365.0}


@retry_on_exception(max_retries=3, delay=0.05, backoff=1.5)
def charge(payment_id: str, amount: float, borrower_id: str) -> Dict[str, Any]:
    """Charge a payment with retry logic and exception safety."""
    if not payment_id or amount <= 0:
        raise ValueError("Invalid payment_id or amount for charge operation")

    record = {
        "payment_id": payment_id,
        "amount": amount,
        "borrower_id": borrower_id,
        "status": "charged",
    }
    _PAYMENTS_DB[payment_id] = record
    logger.info("Payment charged successfully: %s", payment_id)
    return record


def get_payment(payment_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve payment details safely without escaping unhandled exceptions."""
    try:
        if payment_id not in _PAYMENTS_DB:
            logger.warning("Payment not found: %s", payment_id)
            return None
        return _PAYMENTS_DB[payment_id]
    except Exception as exc:
        logger.error("Error retrieving payment %s: %s", payment_id, exc)
        return None


@retry_on_exception(max_retries=3, delay=0.05, backoff=1.5)
def refund(payment_id: str, amount: Optional[float] = None) -> Dict[str, Any]:
    """Refund a payment with retry logic and error handling."""
    payment = get_payment(payment_id)
    if not payment:
        raise KeyError(f"Payment {payment_id} not found for refund")

    refund_amount = amount if amount is not None else payment["amount"]
    if refund_amount <= 0 or refund_amount > payment["amount"]:
        raise ValueError(f"Invalid refund amount {refund_amount}")

    payment["status"] = "refunded"
    payment["refund_amount"] = refund_amount
    _PAYMENTS_DB[payment_id] = payment
    logger.info("Payment %s refunded successfully: %.2f", payment_id, refund_amount)
    return payment


def process_payment(payment_id: str, amount: float, borrower_id: str) -> Dict[str, Any]:
    """Process a payment record with full exception handling."""
    try:
        return charge(payment_id, amount, borrower_id)
    except Exception as exc:
        logger.error("Failed to process payment %s: %s", payment_id, exc)
        raise
