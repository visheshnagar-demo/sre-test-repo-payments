"""Unit tests for calculate_late_fee."""

import pytest
from server.calculator import DAILY_RATE, calculate_late_fee


def test_normal_calculation():
    result = calculate_late_fee(1000.0, 30, 3)
    expected_fee = round((1000.0 * DAILY_RATE * 30) / 3, 2)
    assert result["late_fee"] == expected_fee
    assert result["principal"] == 1000.0
    assert result["overdue_days"] == 30
    assert result["installment_count"] == 3


def test_zero_overdue_days():
    result = calculate_late_fee(1000.0, 0, 3)
    assert result["late_fee"] == 0.0


def test_zero_installments_returns_zero():
    """Verify that installment_count=0 returns late_fee=0.0 without ZeroDivisionError."""
    result = calculate_late_fee(1000.0, 30, 0)
    assert result["late_fee"] == 0.0
    assert result["installment_count"] == 0


def test_negative_installments_returns_zero():
    result = calculate_late_fee(1000.0, 30, -1)
    assert result["late_fee"] == 0.0


def test_single_installment():
    result = calculate_late_fee(500.0, 10, 1)
    expected_fee = round(500.0 * DAILY_RATE * 10, 2)
    assert result["late_fee"] == expected_fee


def test_large_principal_rounding():
    result = calculate_late_fee(500000.0, 90, 24)
    assert isinstance(result["late_fee"], float)
    assert result["late_fee"] > 0


def test_retry_and_exception_safety():
    """Verify calculate_late_fee handles zero/negative installments and retries without raising exception."""
    result = calculate_late_fee(5000.0, 15, 0, max_retries=2)
    assert result["late_fee"] == 0.0
    assert "daily_rate" in result
