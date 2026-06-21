import os
import sys

# Ensure parent directory of 'app' is in python path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from sqlalchemy.orm import Session
from app.db import models
from app import schemas
from datetime import datetime

# Patient CRUD
def get_patient_by_phone(db: Session, phone_number: str):
    return db.query(models.Patient).filter(models.Patient.phone_number == phone_number).first()

def create_patient(db: Session, patient: schemas.PatientCreate):
    db_patient = models.Patient(
        name=patient.name,
        phone_number=patient.phone_number,
        email=patient.email,
        dob=patient.dob
    )
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    return db_patient

# Doctor CRUD
def get_doctor(db: Session, doctor_id: int):
    return db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()

def get_doctors(db: Session):
    return db.query(models.Doctor).all()

# Appointment CRUD
def get_patient_appointments(db: Session, patient_id: int):
    return db.query(models.Appointment).filter(
        models.Appointment.patient_id == patient_id
    ).all()

def get_appointment(db: Session, appointment_id: int):
    return db.query(models.Appointment).filter(models.Appointment.id == appointment_id).first()

def create_appointment(db: Session, appointment: schemas.AppointmentCreate):
    db_appointment = models.Appointment(
        patient_id=appointment.patient_id,
        doctor_id=appointment.doctor_id,
        date_time=appointment.date_time,
        reason=appointment.reason,
        status="Scheduled"
    )
    db.add(db_appointment)
    db.commit()
    db.refresh(db_appointment)
    return db_appointment

def reschedule_appointment(db: Session, appointment_id: int, new_date_time: str):
    db_appointment = get_appointment(db, appointment_id)
    if db_appointment:
        db_appointment.date_time = new_date_time
        db_appointment.status = "Rescheduled"
        db.commit()
        db.refresh(db_appointment)
    return db_appointment

def cancel_appointment(db: Session, appointment_id: int):
    db_appointment = get_appointment(db, appointment_id)
    if db_appointment:
        db_appointment.status = "Cancelled"
        db.commit()
        db.refresh(db_appointment)
    return db_appointment

# Billing CRUD
def get_patient_billing(db: Session, patient_id: int):
    return db.query(models.Billing).filter(models.Billing.patient_id == patient_id).all()

def pay_invoice(db: Session, invoice_id: int):
    db_billing = db.query(models.Billing).filter(models.Billing.id == invoice_id).first()
    if db_billing:
        db_billing.status = "Paid"
        db.commit()
        db.refresh(db_billing)
    return db_billing
