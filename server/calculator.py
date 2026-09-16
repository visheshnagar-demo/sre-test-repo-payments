"""Loan late-fee calculator with robust exception handling and retry logic."""

import asyncio
import functools
import logging
import time
from typing import Callable, Any, Dict

logger = logging.getLogger(__name__)

ANNUAL_LATE_RATE = 0.18


def retry_on_exception(
    max_retries: int = 3,
    delay: float = 0.1,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
) -> Callable:
    """Decorator to retry a sync or async function on specified exceptions."""

    def decorator(func: Callable) -> Callable:
        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                current_delay = delay
                for attempt in range(1, max_retries + 1):
                    try:
                        return await func(*args, **kwargs)
                    except exceptions as exc:
                        if attempt == max_retries:
                            logger.error(
                                "Function %s failed after %d retries. Error: %s",
                                func.__name__,
                                max_retries,
                                exc,
                            )
                            raise
                        logger.warning(
                            "Attempt %d/%d for %s failed with %s. Retrying in %.2fs...",
                            attempt,
                            max_retries,
                            func.__name__,
                            exc,
                            current_delay,
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff

            return async_wrapper
        else:

            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                current_delay = delay
                for attempt in range(1, max_retries + 1):
                    try:
                        return func(*args, **kwargs)
                    except exceptions as exc:
                        if attempt == max_retries:
                            logger.error(
                                "Function %s failed after %d retries. Error: %s",
                                func.__name__,
                                max_retries,
                                exc,
                            )
                            raise
                        logger.warning(
                            "Attempt %d/%d for %s failed with %s. Retrying in %.2fs...",
                            attempt,
                            max_retries,
                            func.__name__,
                            exc,
                            current_delay,
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff

            return sync_wrapper

    return decorator


def calculate_late_fee(
    principal: float, overdue_days: int, installment_count: int
) -> Dict[str, float]:
    """Calculate penalty for an overdue loan installment.

    Handles ZeroDivisionError and invalid inputs safely, returning late_fee=0.0 when
    installment_count is <= 0 or when division by zero occurs.
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
            logger.warning(
                "calculate_late_fee called with invalid principal=%s or overdue_days=%s",
                principal,
                overdue_days,
            )
            return {"late_fee": 0.0, "daily_rate": daily_rate}

        per_installment = principal / installment_count
        late_fee = per_installment * daily_rate * overdue_days
        return {"late_fee": round(late_fee, 2), "daily_rate": daily_rate}
    except ZeroDivisionError as exc:
        logger.exception(
            "ZeroDivisionError caught in calculate_late_fee for installment_count=%s: %s",
            installment_count,
            exc,
        )
        return {"late_fee": 0.0, "daily_rate": daily_rate}
    except Exception as exc:
        logger.exception("Unexpected error in calculate_late_fee: %s", exc)
        return {"late_fee": 0.0, "daily_rate": daily_rate}
