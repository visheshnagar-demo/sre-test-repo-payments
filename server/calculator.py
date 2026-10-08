import logging
import time

logger = logging.getLogger(__name__)

ANNUAL_RATE = 0.18
DAILY_RATE = ANNUAL_RATE / 365


def calculate_late_fee(
    principal: float,
    overdue_days: int,
    installment_count: int,
    max_retries: int = 3,
    retry_delay: float = 0.05,
) -> dict:
    """Calculate the late fee for an overdue loan payment.

    Formula: (principal * daily_rate * overdue_days) / installment_count
    Handles zero or negative installment_count safely without raising ZeroDivisionError.
    Includes retry logic and structured error logging for observability.
    """
    if installment_count <= 0:
        logger.warning(
            "installment_count is %d (<= 0), returning late_fee=0.0 to prevent ZeroDivisionError. principal=%.2f, overdue_days=%d",
            installment_count,
            principal,
            overdue_days,
        )
        return {
            "principal": principal,
            "overdue_days": overdue_days,
            "installment_count": installment_count,
            "daily_rate": DAILY_RATE,
            "late_fee": 0.0,
        }

    attempt = 0
    last_exception = None

    while attempt < max_retries:
        try:
            late_fee = round(
                (principal * DAILY_RATE * overdue_days) / installment_count, 2
            )
            logger.info(
                "Late fee calculated successfully: principal=%.2f, overdue_days=%d, installment_count=%d, fee=%.2f",
                principal,
                overdue_days,
                installment_count,
                late_fee,
            )
            return {
                "principal": principal,
                "overdue_days": overdue_days,
                "installment_count": installment_count,
                "daily_rate": DAILY_RATE,
                "late_fee": late_fee,
            }
        except ZeroDivisionError:
            logger.error(
                "ZeroDivisionError in calculate_late_fee (attempt %d/%d): installment_count=%d. Returning late_fee=0.0",
                attempt + 1,
                max_retries,
                installment_count,
                exc_info=True,
            )
            return {
                "principal": principal,
                "overdue_days": overdue_days,
                "installment_count": installment_count,
                "daily_rate": DAILY_RATE,
                "late_fee": 0.0,
            }
        except Exception as e:
            last_exception = e
            attempt += 1
            logger.error(
                "Error calculating late fee (attempt %d/%d): %s",
                attempt,
                max_retries,
                str(e),
                exc_info=True,
            )
            if attempt < max_retries:
                time.sleep(retry_delay)

    logger.error(
        "All %d attempts failed in calculate_late_fee. Returning fallback fee 0.0. Last exception: %s",
        max_retries,
        str(last_exception),
        exc_info=True,
    )
    return {
        "principal": principal,
        "overdue_days": overdue_days,
        "installment_count": installment_count,
        "daily_rate": DAILY_RATE,
        "late_fee": 0.0,
    }
