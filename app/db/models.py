import os
import sys

# Ensure parent directory of 'app' is in python path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    phone_number = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, nullable=True)
    dob = Column(String, nullable=True)

    appointments = relationship("Appointment", back_populates="patient", cascade="all, delete-orphan")
    billings = relationship("Billing", back_populates="patient", cascade="all, delete-orphan")


class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    specialty = Column(String, nullable=False)
    available_hours = Column(String, nullable=False)  # e.g. "Mon-Fri 09:00-17:00"
    consultation_fee = Column(Float, nullable=False)

    appointments = relationship("Appointment", back_populates="doctor", cascade="all, delete-orphan")


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    date_time = Column(String, nullable=False)  # Store as YYYY-MM-DD HH:MM
    status = Column(String, default="Scheduled")  # "Scheduled", "Rescheduled", "Cancelled"
    reason = Column(String, nullable=True)

    patient = relationship("Patient", back_populates="appointments")
    doctor = relationship("Doctor", back_populates="appointments")


class Billing(Base):
    __tablename__ = "billings"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(String, default="Pending")  # "Pending", "Paid"
    due_date = Column(String, nullable=False)  # Store as YYYY-MM-DD
    details = Column(String, nullable=True)

    patient = relationship("Patient", back_populates="billings")


class RagDoc(Base):
    __tablename__ = "rag_documents"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String, nullable=False)  # e.g., "Doctor Profile", "Clinic Policy", "Billing FAQ"
    title = Column(String, nullable=False)
    content = Column(String, nullable=False)
    keywords = Column(String, nullable=True)
    embedding = Column(String, nullable=True)  # Store embedding as JSON string if calculated
