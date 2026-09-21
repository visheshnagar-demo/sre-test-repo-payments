from fastapi.testclient import TestClient
from server.main import app

client = TestClient(app)


def test_healthz():
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readyz():
    response = client.get("/readyz")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["service"] == "sre-payments-test"


def test_calculate_late_fee_zero_installments():
    response = client.post(
        "/calculate-late-fee",
        json={"principal": 1000.0, "overdue_days": 30, "installment_count": 0},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["late_fee"] == 0.0


def test_calculate_late_fee_normal():
    response = client.post(
        "/calculate-late-fee",
        json={"principal": 1000.0, "overdue_days": 30, "installment_count": 10},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["late_fee"] > 0


def test_process_payment():
    response = client.post(
        "/process-payment",
        json={"payment_id": "pay_123", "amount": 150.0, "borrower_id": "bor_456"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "accepted"
    assert data["payment_id"] == "pay_123"
