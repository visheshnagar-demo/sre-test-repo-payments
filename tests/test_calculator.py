"""Unit tests for calculate_late_fee and retry mechanism in server.calculator."""

import pytest

from server.calculator import calculate_late_fee, retry_on_exception

DAILY_RATE = 0.18 / 365.0


def test_normal_loan_produces_positive_fee():
    result = calculate_late_fee(10000.0, 30, 12)
    assert result["late_fee"] > 0
    assert result["daily_rate"] == pytest.approx(DAILY_RATE, rel=1e-6)


def test_zero_installments_returns_zero():
    """Fully-paid loan (installment_count=0) must return 0.0, not raise ZeroDivisionError."""
    result = calculate_late_fee(10000.0, 30, 0)
    assert result["late_fee"] == 0.0
    assert result["daily_rate"] == pytest.approx(DAILY_RATE, rel=1e-6)


def test_negative_installments_returns_zero():
    """Negative installment_count must return 0.0 safely without error."""
    result = calculate_late_fee(10000.0, 30, -5)
    assert result["late_fee"] == 0.0
    assert result["daily_rate"] == pytest.approx(DAILY_RATE, rel=1e-6)


def test_single_installment_fee_calculation():
    result = calculate_late_fee(1000.0, 10, 1)
    expected = round((1000.0 / 1) * DAILY_RATE * 10, 2)
    assert result["late_fee"] == pytest.approx(expected, rel=1e-6)


def test_large_principal_rounding():
    result = calculate_late_fee(500000.0, 90, 24)
    assert isinstance(result["late_fee"], float)
    assert result["late_fee"] > 0


def test_retry_on_exception_decorator_sync():
    call_count = 0

    @retry_on_exception(max_retries=3, delay=0.01, backoff=1.0)
    def flaky_function():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise ValueError("Transient error")
        return "success"

    res = flaky_function()
    assert res == "success"
    assert call_count == 2


@pytest.mark.anyio
async def test_retry_on_exception_decorator_async():
    call_count = 0

    @retry_on_exception(max_retries=3, delay=0.01, backoff=1.0)
    async def flaky_async_function():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise ValueError("Transient async error")
        return "async_success"

    res = await flaky_async_function()
    assert res == "async_success"
    assert call_count == 2
