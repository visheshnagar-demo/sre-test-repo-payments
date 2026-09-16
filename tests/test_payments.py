"""Unit tests for payment operations in server.payments."""

import pytest

from server.payments import (
    charge,
    get_payment,
    refund,
    safe_calculate_late_fee,
    process_payment,
)


def test_safe_calculate_late_fee_zero_division():
    res = safe_calculate_late_fee(1000.0, 30, 0)
    assert res["late_fee"] == 0.0
    assert "daily_rate" in res


def test_charge_payment():
    payment = charge("PAY-1001", 250.0, "BORROWER-1")
    assert payment["payment_id"] == "PAY-1001"
    assert payment["amount"] == 250.0
    assert payment["status"] == "charged"


def test_charge_invalid_input():
    with pytest.raises(ValueError):
        charge("", -10.0, "BORROWER-1")


def test_get_payment():
    charge("PAY-1002", 500.0, "BORROWER-2")
    fetched = get_payment("PAY-1002")
    assert fetched is not None
    assert fetched["amount"] == 500.0

    not_found = get_payment("NONEXISTENT")
    assert not_found is None


def test_refund_payment():
    charge("PAY-1003", 300.0, "BORROWER-3")
    refunded = refund("PAY-1003", 300.0)
    assert refunded["status"] == "refunded"
    assert refunded["refund_amount"] == 300.0


def test_refund_nonexistent_payment():
    with pytest.raises(KeyError):
        refund("PAY-9999", 100.0)


def test_process_payment():
    res = process_payment("PAY-1004", 150.0, "BORROWER-4")
    assert res["payment_id"] == "PAY-1004"
    assert res["status"] == "charged"
