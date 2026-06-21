import pytest
from fastapi.testclient import TestClient

def test_get_doctors(client: TestClient):
    response = client.get("/api/doctors")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3
    assert data[0]["name"] == "Dr. Jane Smith"

def test_get_patient_by_phone(client: TestClient):
    # Registered patient
    response = client.get("/api/patients/by-phone/%2B919876543210")
    assert response.status_code == 200
    assert response.json()["name"] == "Sarah Jenkins"

    # Non-registered patient
    response = client.get("/api/patients/by-phone/%2B19999999999")
    assert response.status_code == 404

def test_create_patient(client: TestClient):
    payload = {
        "name": "Jim Halpert",
        "phone_number": "+18888888888",
        "email": "jim@dundermifflin.com",
        "dob": "1978-10-01"
    }
    response = client.post("/api/patients", json=payload)
    assert response.status_code == 201
    assert response.json()["name"] == "Jim Halpert"

def test_appointments_flow(client: TestClient):
    # 1. Get patient
    patient_res = client.get("/api/patients/by-phone/%2B919876543210")
    patient_id = patient_res.json()["id"]

    # 2. Get doctors
    doc_res = client.get("/api/doctors")
    doctor_id = doc_res.json()[0]["id"]

    # 3. Create appointment
    payload = {
        "patient_id": patient_id,
        "doctor_id": doctor_id,
        "date_time": "2026-07-15 14:00",
        "reason": "Cardio Checkup"
    }
    create_res = client.post("/api/appointments", json=payload)
    assert create_res.status_code == 201
    appt_id = create_res.json()["id"]

    # 4. Get patient appointments
    get_res = client.get(f"/api/appointments/patient/{patient_id}")
    assert get_res.status_code == 200
    assert any(a["id"] == appt_id for a in get_res.json())

    # 5. Reschedule appointment
    resched_res = client.put(f"/api/appointments/{appt_id}/reschedule", json={"new_date_time": "2026-07-15 15:00"})
    assert resched_res.status_code == 200
    assert resched_res.json()["status"] == "Rescheduled"

    # 6. Cancel appointment
    cancel_res = client.put(f"/api/appointments/{appt_id}/cancel")
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "Cancelled"

def test_billing_flow(client: TestClient):
    patient_res = client.get("/api/patients/by-phone/%2B919876543210")
    patient_id = patient_res.json()["id"]

    # Get billings
    get_res = client.get(f"/api/billing/patient/{patient_id}")
    assert get_res.status_code == 200
    billings = get_res.json()
    assert len(billings) >= 1

    # Find pending billing
    pending_bill = next((b for b in billings if b["status"] == "Pending"), None)
    assert pending_bill is not None
    invoice_id = pending_bill["id"]

    # Pay billing
    pay_res = client.post(f"/api/billing/{invoice_id}/pay")
    assert pay_res.status_code == 200
    assert pay_res.json()["status"] == "Paid"

def test_chat_simulate(client: TestClient):
    payload = {
        "phone_number": "+919876543210",
        "message": "Hi, I have a general query about opening hours."
    }
    response = client.post("/api/chat/simulate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert "patient_name" in data
