"""Loan late-fee calculator with exception safety."""

import logging
from typing import Dict

logger = logging.getLogger(__name__)

ANNUAL_LATE_RATE = 0.18


def calculate_late_fee(
    principal: float, overdue_days: int, installment_count: int
) -> Dict[str, float]:
    """Calculate penalty for an overdue loan installment.

    Returns late_fee=0.0 when installment_count is zero or negative or on error.
    """
    daily_rate = ANNUAL_LATE_RATE / 365.0
    try:
        if not installment_count or installment_count <= 0:
            logger.warning(
                "calculate_late_fee called with installment_count=%s <= 0. Returning late_fee=0.0",
                installment_count,
            )
            return {"late_fee": 0.0, "daily_rate": daily_rate}
        if principal < 0 or overdue_days < 0:
            return {"late_fee": 0.0, "daily_rate": daily_rate}
        per_installment = principal / installment_count
        late_fee = per_installment * daily_rate * overdue_days
        return {"late_fee": round(late_fee, 2), "daily_rate": daily_rate}
    except ZeroDivisionError as exc:
        logger.exception(
            "ZeroDivisionError trapped in calculate_late_fee for installment_count=%s: %s",
            installment_count,
            exc,
        )
        return {"late_fee": 0.0, "daily_rate": daily_rate}
    except Exception as exc:
        logger.exception("Unexpected error trapped in calculate_late_fee: %s", exc)
        return {"late_fee": 0.0, "daily_rate": daily_rate}
