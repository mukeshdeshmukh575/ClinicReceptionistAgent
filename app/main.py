import os
import sys
from dotenv import load_dotenv

# Ensure the parent directory of 'app' is in the python path
# this allows running the app from any working directory and guarantees imports like 'from app import ...' work.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

from app import schemas
from app.db import models, crud, seed
from app.db.database import engine, get_db, SessionLocal
from app.agent import agent

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Aura Wellness Clinic Backend & Clinic Receptionist Agent Simulator",
    description="REST APIs for Doctors, Patients, Appointments, Billing and Clinic Receptionist Agent integration.",
    version="1.0.0"
)

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup Seeding
@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    try:
        seed.seed_db(db)
    finally:
        db.close()


# --- REST API ENDPOINTS ---

# 1. Doctors
@app.get("/api/doctors", response_model=List[schemas.DoctorResponse], tags=["Doctors"])
def read_doctors(db: Session = Depends(get_db)):
    """Retrieve all clinic doctors and their details."""
    return crud.get_doctors(db)

# 2. Patients
@app.get("/api/patients/by-phone/{phone_number}", response_model=schemas.PatientResponse, tags=["Patients"])
def read_patient_by_phone(phone_number: str, db: Session = Depends(get_db)):
    """Fetch patient details by phone number (used in Clinic Receptionist Agent integration)."""
    patient = crud.get_patient_by_phone(db, phone_number)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with phone number {phone_number} not found."
        )
    return patient

@app.post("/api/patients", response_model=schemas.PatientResponse, status_code=status.HTTP_201_CREATED, tags=["Patients"])
def create_new_patient(patient: schemas.PatientCreate, db: Session = Depends(get_db)):
    """Register a new patient."""
    db_patient = crud.get_patient_by_phone(db, patient.phone_number)
    if db_patient:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A patient with this phone number already exists."
        )
    return crud.create_patient(db, patient)

# 3. Appointments
@app.get("/api/appointments/patient/{patient_id}", response_model=List[schemas.AppointmentResponse], tags=["Appointments"])
def read_patient_appointments(patient_id: int, db: Session = Depends(get_db)):
    """List all appointments (scheduled, rescheduled, cancelled) for a patient."""
    return crud.get_patient_appointments(db, patient_id)

@app.post("/api/appointments", response_model=schemas.AppointmentResponse, status_code=status.HTTP_201_CREATED, tags=["Appointments"])
def book_new_appointment(appointment: schemas.AppointmentCreate, db: Session = Depends(get_db)):
    """Book a new appointment slot."""
    # Check patient exists
    patient = db.query(models.Patient).filter(models.Patient.id == appointment.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found.")
        
    # Check doctor exists
    doctor = crud.get_doctor(db, appointment.doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found.")
        
    return crud.create_appointment(db, appointment)

@app.put("/api/appointments/{id}/reschedule", response_model=schemas.AppointmentResponse, tags=["Appointments"])
def reschedule_existing_appointment(id: int, payload: schemas.AppointmentReschedule, db: Session = Depends(get_db)):
    """Reschedule an existing appointment."""
    appt = crud.get_appointment(db, id)
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found.")
    return crud.reschedule_appointment(db, id, payload.new_date_time)

@app.put("/api/appointments/{id}/cancel", response_model=schemas.AppointmentResponse, tags=["Appointments"])
def cancel_existing_appointment(id: int, db: Session = Depends(get_db)):
    """Cancel an appointment."""
    appt = crud.get_appointment(db, id)
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found.")
    return crud.cancel_appointment(db, id)

# 4. Billing & Payments
@app.get("/api/billing/patient/{patient_id}", response_model=List[schemas.BillingResponse], tags=["Billing"])
def read_patient_billing(patient_id: int, db: Session = Depends(get_db)):
    """Get billing details and invoice logs for a patient."""
    return crud.get_patient_billing(db, patient_id)

@app.post("/api/billing/{invoice_id}/pay", response_model=schemas.BillingResponse, tags=["Billing"])
def mark_invoice_paid(invoice_id: int, db: Session = Depends(get_db)):
    """Process dummy payment for an invoice and mark it as Paid."""
    bill = db.query(models.Billing).filter(models.Billing.id == invoice_id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Invoice not found.")
    return crud.pay_invoice(db, invoice_id)


# --- CLINIC RECEPTIONIST AGENT ROUTE ---

@app.post("/api/chat/simulate", response_model=schemas.ChatResponse, tags=["Clinic Receptionist Agent"])
def chat_simulate(payload: schemas.ChatRequest, db: Session = Depends(get_db)):
    """
    Handles conversation requests from the Web Widget. It processes the sender's phone number and message
    using the guardrails and conversational agent (Gemini AI + RAG DB).
    """
    response_data = agent.generate_agent_response(db, payload.phone_number, payload.message)
    return response_data


# --- STATIC FILE SERVING FOR SIMULATOR FRONTEND ---
frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")
app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
