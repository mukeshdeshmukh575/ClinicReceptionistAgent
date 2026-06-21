from sqlalchemy.orm import Session
from app.db import crud, models
from app import schemas

def test_get_patient_by_phone(db_session: Session):
    # Test getting seeded patient
    patient = crud.get_patient_by_phone(db_session, "+919876543210")
    assert patient is not None
    assert patient.name == "Sarah Jenkins"
    assert patient.email == "sarah.jenkins@example.com"

    # Test getting non-existent patient
    assert crud.get_patient_by_phone(db_session, "+19999999999") is None

def test_create_patient(db_session: Session):
    patient_data = schemas.PatientCreate(
        name="Bob Vance",
        phone_number="+17777777777",
        email="bob@vancefrigeration.com",
        dob="1970-05-12"
    )
    new_patient = crud.create_patient(db_session, patient_data)
    assert new_patient.id is not None
    assert new_patient.name == "Bob Vance"
    
    # Retrieve to confirm
    retrieved = crud.get_patient_by_phone(db_session, "+17777777777")
    assert retrieved is not None
    assert retrieved.name == "Bob Vance"

def test_get_doctors(db_session: Session):
    doctors = crud.get_doctors(db_session)
    assert len(doctors) >= 3
    assert any(d.name == "Dr. Jane Smith" for d in doctors)

def test_get_doctor(db_session: Session):
    doctors = crud.get_doctors(db_session)
    doc_id = doctors[0].id
    doctor = crud.get_doctor(db_session, doc_id)
    assert doctor is not None
    assert doctor.name == doctors[0].name

def test_appointments(db_session: Session):
    patient = crud.get_patient_by_phone(db_session, "+919876543210")
    doctors = crud.get_doctors(db_session)
    doctor = doctors[0]
    
    # Create appointment
    appt_data = schemas.AppointmentCreate(
        patient_id=patient.id,
        doctor_id=doctor.id,
        date_time="2026-07-01 10:00",
        reason="Consultation"
    )
    appt = crud.create_appointment(db_session, appt_data)
    assert appt.id is not None
    assert appt.status == "Scheduled"
    
    # Get patient appointments
    appts = crud.get_patient_appointments(db_session, patient.id)
    assert len(appts) >= 1
    
    # Get single appointment
    retrieved = crud.get_appointment(db_session, appt.id)
    assert retrieved is not None
    assert retrieved.date_time == "2026-07-01 10:00"
    
    # Reschedule
    rescheduled = crud.reschedule_appointment(db_session, appt.id, "2026-07-01 11:00")
    assert rescheduled.status == "Rescheduled"
    assert rescheduled.date_time == "2026-07-01 11:00"
    
    # Cancel
    cancelled = crud.cancel_appointment(db_session, appt.id)
    assert cancelled.status == "Cancelled"

def test_billing(db_session: Session):
    patient = crud.get_patient_by_phone(db_session, "+919876543210")
    
    # Get billing details
    billings = crud.get_patient_billing(db_session, patient.id)
    assert len(billings) >= 1
    
    # Find a pending billing
    pending_bill = next((b for b in billings if b.status == "Pending"), None)
    assert pending_bill is not None
    
    # Pay billing
    paid_bill = crud.pay_invoice(db_session, pending_bill.id)
    assert paid_bill.status == "Paid"
