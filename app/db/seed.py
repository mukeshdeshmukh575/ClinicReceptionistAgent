import os
import sys

# Ensure parent directory of 'app' is in python path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from sqlalchemy.orm import Session
from app.db import models
from app.agent import rag_store

def seed_db(db: Session):
    # Check if database is already seeded
    if db.query(models.Doctor).first() is not None:
        print("Database already seeded.")
        return

    print("Seeding database...")

    # 1. Seed Doctors
    doctors = [
        models.Doctor(
            name="Dr. Jane Smith",
            specialty="Cardiologist",
            available_hours="Mon-Wed 09:00-14:00",
            consultation_fee=150.0
        ),
        models.Doctor(
            name="Dr. Alan Turing",
            specialty="Neurologist",
            available_hours="Thu-Fri 10:00-16:00",
            consultation_fee=200.0
        ),
        models.Doctor(
            name="Dr. Grace Hopper",
            specialty="General Physician",
            available_hours="Mon-Fri 08:00-12:00",
            consultation_fee=100.0
        )
    ]
    db.add_all(doctors)
    db.commit()

    # 2. Seed Patients
    patients = [
        models.Patient(
            name="Sarah Jenkins",
            phone_number="+919876543210",
            email="sarah.jenkins@example.com",
            dob="1985-08-20"
        ),
        models.Patient(
            name="John Doe",
            phone_number="+15551234567",
            email="john.doe@example.com",
            dob="1990-01-01"
        )
    ]
    db.add_all(patients)
    db.commit()

    # Refresh patients to get IDs
    p_sarah = db.query(models.Patient).filter_by(phone_number="+919876543210").first()
    p_john = db.query(models.Patient).filter_by(phone_number="+15551234567").first()

    # 3. Seed Appointments
    appointments = [
        models.Appointment(
            patient_id=p_sarah.id,
            doctor_id=doctors[0].id,  # Dr. Jane Smith
            date_time="2026-06-25 10:00",
            status="Scheduled",
            reason="Routine cardiovascular checkup"
        ),
        models.Appointment(
            patient_id=p_john.id,
            doctor_id=doctors[2].id,  # Dr. Grace Hopper
            date_time="2026-06-22 09:00",
            status="Scheduled",
            reason="Annual checkup"
        )
    ]
    db.add_all(appointments)
    db.commit()

    # 4. Seed Billings
    billings = [
        models.Billing(
            patient_id=p_sarah.id,
            amount=150.0,
            status="Pending",
            due_date="2026-06-30",
            details="Consultation charge for upcoming appointment with Dr. Jane Smith"
        ),
        models.Billing(
            patient_id=p_sarah.id,
            amount=75.0,
            status="Paid",
            due_date="2026-06-10",
            details="Pharmacy medication charges"
        ),
        models.Billing(
            patient_id=p_john.id,
            amount=100.0,
            status="Paid",
            due_date="2026-06-20",
            details="Consultation charge for General Physician visit"
        )
    ]
    db.add_all(billings)
    db.commit()

    # 5. Seed RAG FAQs and Policies
    # We use rag_store.add_rag_document so embeddings are generated if API key is present
    rag_docs = [
        {
            "category": "Clinic Info",
            "title": "Clinic Opening Hours & Operational Timing",
            "content": "Aura Wellness Clinic is open Monday to Friday, from 8:00 AM to 5:00 PM. We are closed on Saturdays, Sundays, and all major national holidays. Emergency consultations are not available outside these hours.",
            "keywords": "hours, timings, open, close, schedule, days, working, weekend"
        },
        {
            "category": "Clinic Info",
            "title": "Clinic Location and Address",
            "content": "Aura Wellness Clinic is located at 123 Health Avenue, Suite 400, Medical District, Cityville. Convenient parking is available in the basement structure, with free validation for the first 2 hours of your visit.",
            "keywords": "address, location, map, directions, find, parking, office, room, suite, floor"
        },
        {
            "category": "Clinic Policy",
            "title": "Cancellation, Rescheduling, and Refund Policies",
            "content": "Patients must reschedule or cancel their appointments at least 24 hours prior to the scheduled slot. Cancellations made less than 24 hours in advance may be subject to a late cancellation fee equal to 50% of the consultation charge. No-shows without notice will be billed for the full consultation fee.",
            "keywords": "cancel, reschedule, policy, late, refund, fee, penalty, charge, delay, no show"
        },
        {
            "category": "Clinic Policy",
            "title": "Insurance Coverage and Accepted Providers",
            "content": "We accept major insurance providers including Aetna, Blue Cross Blue Shield, Cigna, UnitedHealthcare, and Medicare. Please provide your insurance policy details during registration or upload them via our patient portal. Co-payments are due at the time of your check-in.",
            "keywords": "insurance, provider, aetna, cigna, blue cross, medicare, pay, co-pay, coverage"
        },
        {
            "category": "Emergency Policy",
            "title": "Medical Emergency Warning and Guidelines",
            "content": "Aura Wellness Clinic does NOT handle emergency medical requests. If you are experiencing a life-threatening medical emergency, chest pains, shortness of breath, severe bleeding, or trauma, please immediately dial 911 (or your local emergency services) or proceed to the nearest Emergency Room.",
            "keywords": "emergency, pain, breath, trauma, bleeding, hospital, er, 911, death, critical, urgent"
        },
        {
            "category": "Billing FAQ",
            "title": "Payment Reminders and Methods of Payment",
            "content": "Payment reminders are sent automatically via Email and Web Widget notifications for invoices that are within 5 days of their due date. We support payments through online credit/debit card portals, UPI, PayPal, and bank transfers. Check payment links generated by the Web Booking system to pay instantly.",
            "keywords": "payment, bill, pay, reminder, card, credit, debit, bank, upi, link, paypal"
        }
    ]

    for doc in rag_docs:
        rag_store.add_rag_document(
            db,
            category=doc["category"],
            title=doc["title"],
            content=doc["content"],
            keywords=doc["keywords"]
        )

    print("Database seeding completed.")
