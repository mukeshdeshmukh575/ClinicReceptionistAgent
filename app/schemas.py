from pydantic import BaseModel, Field
from typing import List, Optional

# Patient schemas
class PatientBase(BaseModel):
    name: str
    phone_number: str
    email: Optional[str] = None
    dob: Optional[str] = None

class PatientCreate(PatientBase):
    pass

class PatientResponse(PatientBase):
    id: int

    class Config:
        from_attributes = True

# Doctor schemas
class DoctorBase(BaseModel):
    name: str
    specialty: str
    available_hours: str
    consultation_fee: float

class DoctorCreate(DoctorBase):
    pass

class DoctorResponse(DoctorBase):
    id: int

    class Config:
        from_attributes = True

# Appointment schemas
class AppointmentBase(BaseModel):
    patient_id: int
    doctor_id: int
    date_time: str
    reason: Optional[str] = None

class AppointmentCreate(AppointmentBase):
    pass

class AppointmentReschedule(BaseModel):
    new_date_time: str

class AppointmentResponse(AppointmentBase):
    id: int
    status: str
    patient: Optional[PatientResponse] = None
    doctor: Optional[DoctorResponse] = None

    class Config:
        from_attributes = True

# Billing schemas
class BillingBase(BaseModel):
    patient_id: int
    amount: float
    status: str = "Pending"
    due_date: str
    details: Optional[str] = None

class BillingCreate(BillingBase):
    pass

class BillingResponse(BillingBase):
    id: int

    class Config:
        from_attributes = True

class PaymentRequest(BaseModel):
    invoice_id: int

# Chat Simulator schemas
class ChatRequest(BaseModel):
    phone_number: str
    message: str

class ChatResponse(BaseModel):
    reply: str
    patient_name: Optional[str] = None
    escalated: bool = False
    weird_flag: bool = False
    logs: List[str] = []
    rag_sources: List[str] = []
