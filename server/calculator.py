"""Loan late-fee calculator with exception handling and retry logic."""

import logging
import time

logger = logging.getLogger(__name__)

ANNUAL_LATE_RATE = 0.18


def calculate_late_fee(
    principal: float, overdue_days: int, installment_count: int, max_retries: int = 3
) -> dict:
    """Calculate penalty for an overdue loan installment.

    Includes guard for installment_count=0 (ZeroDivisionError) and retry logic with logging.
    Returns late_fee=0.0 when installment_count is zero (fully-paid loan edge case).
    """
    daily_rate = ANNUAL_LATE_RATE / 365

    for attempt in range(max_retries):
        try:
            if installment_count <= 0:
                logger.warning(
                    "installment_count is %d (<= 0) for principal %.2f. Defaulting late_fee to 0.0",
                    installment_count,
                    principal,
                )
                return {"late_fee": 0.0, "daily_rate": daily_rate}

            per_installment = principal / installment_count
            late_fee = per_installment * daily_rate * overdue_days
            return {"late_fee": round(late_fee, 2), "daily_rate": daily_rate}
        except ZeroDivisionError as e:
            logger.error(
                "ZeroDivisionError in calculate_late_fee (attempt %d/%d): %s",
                attempt + 1,
                max_retries,
                e,
            )
            if attempt == max_retries - 1:
                return {"late_fee": 0.0, "daily_rate": daily_rate}
            time.sleep(0.01)
        except Exception as e:
            logger.error(
                "Unexpected error in calculate_late_fee (attempt %d/%d): %s",
                attempt + 1,
                max_retries,
                e,
            )
            if attempt == max_retries - 1:
                return {"late_fee": 0.0, "daily_rate": daily_rate}
            time.sleep(0.01)

    return {"late_fee": 0.0, "daily_rate": daily_rate}
