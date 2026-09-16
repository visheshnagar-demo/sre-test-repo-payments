"""Integration tests for FastAPI endpoints in server.main."""

import pytest


def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["service"] == "sre-payments-test"
    assert json_data["status"] == "running"


def test_healthz_endpoint(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readyz_endpoint(client):
    response = client.get("/readyz")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_calculate_late_fee_endpoint_success(client):
    payload = {
        "principal": 1000.0,
        "overdue_days": 30,
        "installment_count": 12,
    }
    response = client.post("/calculate-late-fee", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "late_fee" in data
    assert "daily_rate" in data
    assert data["late_fee"] > 0


def test_calculate_late_fee_endpoint_zero_installments(client):
    """Verify installment_count=0 returns 200 with late_fee=0.0 and does not crash or raise uncaught ZeroDivisionError."""
    payload = {
        "principal": 1000.0,
        "overdue_days": 30,
        "installment_count": 0,
    }
    response = client.post("/calculate-late-fee", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["late_fee"] == 0.0


def test_process_payment_endpoint(client):
    payload = {
        "payment_id": "API-PAY-01",
        "amount": 200.0,
        "borrower_id": "USER-01",
    }
    response = client.post("/process-payment", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["payment_id"] == "API-PAY-01"
    assert data["status"] == "accepted" or data["status"] == "charged"


def test_charge_endpoint(client):
    payload = {
        "payment_id": "CHARGE-01",
        "amount": 150.0,
        "borrower_id": "USER-02",
    }
    response = client.post("/charge", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["payment_id"] == "CHARGE-01"


def test_get_payment_endpoint_found_and_404(client):
    # Charge first
    payload = {
        "payment_id": "GET-PAY-01",
        "amount": 100.0,
        "borrower_id": "USER-03",
    }
    client.post("/charge", json=payload)

    # Get existing
    res = client.get("/payments/GET-PAY-01")
    assert res.status_code == 200
    assert res.json()["amount"] == 100.0

    # Get non-existent
    res_404 = client.get("/payments/NONEXISTENT-PAYMENT")
    assert res_404.status_code == 404
    assert "detail" in res_404.json()


def test_refund_endpoint(client):
    # Charge first
    charge_payload = {
        "payment_id": "REFUND-PAY-01",
        "amount": 80.0,
        "borrower_id": "USER-04",
    }
    client.post("/charge", json=charge_payload)

    # Refund
    refund_payload = {
        "payment_id": "REFUND-PAY-01",
        "amount": 80.0,
    }
    res = client.post("/refund", json=refund_payload)
    assert res.status_code == 200
    assert res.json()["status"] == "refunded"
