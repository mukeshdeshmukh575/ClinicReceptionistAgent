import os
import sys
from dotenv import load_dotenv

# Ensure parent directory of 'app' is in python path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Load environment variables
load_dotenv()

import json
from sqlalchemy.orm import Session
import google.generativeai as genai
from app.db import crud, models
from app.agent import rag_store

# Configure Gemini API
api_key = os.getenv("GEMINI_API_KEY")
gemini_model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
if api_key:
    genai.configure(api_key=api_key)
else:
    print("Warning: GEMINI_API_KEY environment variable is not set. Chat features will run in mock mode.")

# Safety / Acceptability Screen
def screen_incoming_message(message: str) -> tuple[bool, str]:
    """
    Checks if the incoming message is weird, unacceptable, or contains prompt injections.
    Returns (is_unacceptable, warning_response).
    """
    msg_lower = message.strip().lower()
    if not msg_lower:
        return True, "It looks like your message is empty. How can I help you with appointments or billing?"

    # Prompt injection check
    injection_triggers = [
        "ignore previous", "ignore above", "forget your instructions", "forget my previous",
        "system prompt", "you are now an assistant of", "bypass restrictions",
        "jailbreak", "override instructions", "dan mode", "developer mode"
    ]
    for trigger in injection_triggers:
        if trigger in msg_lower:
            return True, "Invalid request. I can only assist with scheduling, account details, and billing queries."

    # Inappropriate/vulgar content screening
    vulgarities = ["fuck", "shit", "bitch", "asshole", "bastard", "cunt", "dick", "pussy", "idiot", "suck", "retard"]
    for word in vulgarities:
        if word in msg_lower:
            return True, "We do not tolerate inappropriate language. Please keep your queries focused on clinic scheduling and billing."

    # Gibberish check (e.g. extremely long string without spaces)
    if len(message) > 30 and " " not in message:
        return True, "We could not understand your message. Please send a readable request regarding appointments or billing."

    return False, ""


class ClinicTools:
    """
    Tools that the Gemini agent can call to interface with the clinic's REST database and RAG store.
    All actions are scoped to the sender's phone number.
    """
    def __init__(self, db: Session, phone_number: str, logs_list: list, rag_sources_list: list):
        self.db = db
        self.phone_number = phone_number
        self.logs = logs_list
        self.rag_sources = rag_sources_list
        self.escalated = False

    def get_patient_details(self) -> str:
        """
        Retrieves the profile details of the current patient based on their phone number.
        Returns:
            str: JSON representation of the patient profile, or a message indicating not found.
        """
        self.logs.append("Tool Call: get_patient_details")
        patient = crud.get_patient_by_phone(self.db, self.phone_number)
        if patient:
            return json.dumps({
                "patient_id": patient.id,
                "name": patient.name,
                "phone_number": patient.phone_number,
                "email": patient.email,
                "dob": patient.dob
            })
        return json.dumps({"error": "Patient profile not found. Please register."})

    def register_patient(self, name: str, email: str, dob: str) -> str:
        """
        Registers a new patient with the clinic.
        Args:
            name: The full name of the patient.
            email: The email address of the patient.
            dob: The date of birth of the patient (format YYYY-MM-DD).
        Returns:
            str: Confirmation message with patient details.
        """
        self.logs.append(f"Tool Call: register_patient(name={name}, email={email}, dob={dob})")
        from app.schemas import PatientCreate
        patient_data = PatientCreate(
            name=name,
            phone_number=self.phone_number,
            email=email,
            dob=dob
        )
        patient = crud.create_patient(self.db, patient_data)
        return json.dumps({
            "message": "Registration successful!",
            "patient_id": patient.id,
            "name": patient.name
        })

    def list_doctors(self) -> str:
        """
        Lists all the doctors working at the clinic, their specialties, consultation fees, and available hours.
        Returns:
            str: JSON list of available doctors.
        """
        self.logs.append("Tool Call: list_doctors")
        doctors = crud.get_doctors(self.db)
        return json.dumps([{
            "doctor_id": doc.id,
            "name": doc.name,
            "specialty": doc.specialty,
            "available_hours": doc.available_hours,
            "consultation_fee": doc.consultation_fee
        } for doc in doctors])

    def book_appointment(self, doctor_id: int, date_time: str, reason: str) -> str:
        """
        Schedules a new appointment with a doctor.
        Args:
            doctor_id: The ID of the doctor.
            date_time: The date and time for the appointment (format YYYY-MM-DD HH:MM).
            reason: The reason for booking.
        Returns:
            str: JSON representation of the booked appointment or an error message.
        """
        self.logs.append(f"Tool Call: book_appointment(doctor={doctor_id}, time={date_time}, reason={reason})")
        patient = crud.get_patient_by_phone(self.db, self.phone_number)
        if not patient:
            return json.dumps({"error": "You must be registered before booking an appointment."})
        
        from app.schemas import AppointmentCreate
        appointment_data = AppointmentCreate(
            patient_id=patient.id,
            doctor_id=doctor_id,
            date_time=date_time,
            reason=reason
        )
        # Verify doctor exists
        doctor = crud.get_doctor(self.db, doctor_id)
        if not doctor:
            return json.dumps({"error": f"Doctor with ID {doctor_id} not found."})

        # Book
        appt = crud.create_appointment(self.db, appointment_data)
        return json.dumps({
            "message": "Appointment scheduled successfully!",
            "appointment_id": appt.id,
            "doctor": doctor.name,
            "date_time": appt.date_time,
            "status": appt.status
        })

    def get_upcoming_appointments(self) -> str:
        """
        Retrieves all active appointments for the patient.
        Returns:
            str: JSON list of upcoming appointments.
        """
        self.logs.append("Tool Call: get_upcoming_appointments")
        patient = crud.get_patient_by_phone(self.db, self.phone_number)
        if not patient:
            return json.dumps({"error": "No patient record found for this number."})
            
        appointments = crud.get_patient_appointments(self.db, patient.id)
        active_appts = [a for a in appointments if a.status in ["Scheduled", "Rescheduled"]]
        return json.dumps([{
            "appointment_id": a.id,
            "doctor": a.doctor.name,
            "specialty": a.doctor.specialty,
            "date_time": a.date_time,
            "status": a.status,
            "reason": a.reason
        } for a in active_appts])

    def reschedule_appointment(self, appointment_id: int, new_date_time: str) -> str:
        """
        Reschedules an existing appointment to a new date and time.
        Args:
            appointment_id: The ID of the appointment to reschedule.
            new_date_time: The new date and time (format YYYY-MM-DD HH:MM).
        Returns:
            str: JSON representation of the rescheduled appointment or an error message.
        """
        self.logs.append(f"Tool Call: reschedule_appointment(id={appointment_id}, new_time={new_date_time})")
        patient = crud.get_patient_by_phone(self.db, self.phone_number)
        if not patient:
            return json.dumps({"error": "No patient record found."})

        # Verify appointment belongs to patient
        appt = crud.get_appointment(self.db, appointment_id)
        if not appt or appt.patient_id != patient.id:
            return json.dumps({"error": "Appointment not found or does not belong to you."})

        res_appt = crud.reschedule_appointment(self.db, appointment_id, new_date_time)
        return json.dumps({
            "message": "Appointment rescheduled successfully!",
            "appointment_id": res_appt.id,
            "new_date_time": res_appt.date_time,
            "status": res_appt.status
        })

    def cancel_appointment(self, appointment_id: int) -> str:
        """
        Cancels an existing appointment.
        Args:
            appointment_id: The ID of the appointment to cancel.
        Returns:
            str: JSON response confirming cancellation.
        """
        self.logs.append(f"Tool Call: cancel_appointment(id={appointment_id})")
        patient = crud.get_patient_by_phone(self.db, self.phone_number)
        if not patient:
            return json.dumps({"error": "No patient record found."})

        # Verify appointment belongs to patient
        appt = crud.get_appointment(self.db, appointment_id)
        if not appt or appt.patient_id != patient.id:
            return json.dumps({"error": "Appointment not found or does not belong to you."})

        cancel_appt = crud.cancel_appointment(self.db, appointment_id)
        return json.dumps({
            "message": "Appointment cancelled successfully.",
            "appointment_id": cancel_appt.id,
            "status": cancel_appt.status
        })

    def get_billing_details(self) -> str:
        """
        Retrieves all invoices, billing records, and payment history for the patient.
        Returns:
            str: JSON list of billing records.
        """
        self.logs.append("Tool Call: get_billing_details")
        patient = crud.get_patient_by_phone(self.db, self.phone_number)
        if not patient:
            return json.dumps({"error": "No patient record found."})

        bills = crud.get_patient_billing(self.db, patient.id)
        return json.dumps([{
            "invoice_id": b.id,
            "amount": b.amount,
            "status": b.status,
            "due_date": b.due_date,
            "details": b.details
        } for b in bills])

    def pay_invoice(self, invoice_id: int) -> str:
        """
        Processes payment for a pending invoice.
        Args:
            invoice_id: The ID of the invoice/bill to pay.
        Returns:
            str: JSON response confirming payment success.
        """
        self.logs.append(f"Tool Call: pay_invoice(id={invoice_id})")
        patient = crud.get_patient_by_phone(self.db, self.phone_number)
        if not patient:
            return json.dumps({"error": "No patient record found."})

        # Verify invoice belongs to patient
        bills = crud.get_patient_billing(self.db, patient.id)
        bill_ids = [b.id for b in bills]
        if invoice_id not in bill_ids:
            return json.dumps({"error": "Invoice not found or does not belong to you."})

        paid_bill = crud.pay_invoice(self.db, invoice_id)
        return json.dumps({
            "message": "Payment successful!",
            "invoice_id": paid_bill.id,
            "amount": paid_bill.amount,
            "status": paid_bill.status
        })

    def search_clinic_knowledge_base(self, query: str) -> str:
        """
        Searches the clinic knowledge base (RAG database) for FAQs, clinic policies, location, or timings.
        Args:
            query: The search query.
        Returns:
            str: Matching information snippets.
        """
        self.logs.append(f"Tool Call: search_clinic_knowledge_base(query='{query}')")
        results = rag_store.search_rag(self.db, query, limit=2)
        if not results:
            return json.dumps({"message": "No matching clinic policies or FAQs found. Please query a human receptionist if unsure."})
            
        snippets = []
        for doc, score in results:
            self.rag_sources.append(f"{doc.title} (Category: {doc.category})")
            snippets.append({
                "title": doc.title,
                "category": doc.category,
                "content": doc.content
            })
        return json.dumps(snippets)

    def escalate_to_human_receptionist(self, reason: str) -> str:
        """
        Escalates the chat to a human receptionist. Use this whenever the patient asks for medical advice,
        makes personal/social remarks, or has custom issues that are out-of-scope.
        Args:
            reason: Explanation of why the ticket is being escalated.
        Returns:
            str: Escalation confirmation message.
        """
        self.logs.append(f"Tool Call: escalate_to_human_receptionist(reason='{reason}')")
        self.escalated = True
        return json.dumps({
            "message": "Conversation is being escalated to a human receptionist.",
            "reason": reason
        })


# System Prompt
SYSTEM_PROMPT = """
You are Aria, the intelligent, friendly, and efficient virtual receptionist for Aura Wellness Clinic.
You communicate via a browser-based web chat widget overlay. Keep your responses conversational, warm, polite, and concise (ideal for a chat screen).

YOUR ROLES AND BOUNDS:
1. SENDER IDENTITY: You are communicating with a patient whose phone number is supplied to you implicitly.
   Your first step should be checking if they have a profile by calling `get_patient_details`.
   - If they are NOT registered, greet them and politely guide them to register by providing their name, email, and DOB (YYYY-MM-DD) via `register_patient`.
   - If they are registered, address them by their name and answer their queries contextually.

2. SUPPORTED TOPICS (IN-SCOPE):
   - Scheduling appointments: List doctors using `list_doctors`, check availability, and book using `book_appointment`.
   - Modifying appointments: View appointments via `get_upcoming_appointments`, reschedule using `reschedule_appointment`, or cancel using `cancel_appointment`.
   - Account details: Return details from `get_patient_details`.
   - Billing & Payments: Retrieve details using `get_billing_details` and process a payment simulation with `pay_invoice`.
   - General Clinic Information: Answer queries about opening hours, location, policies, or general FAQs using `search_clinic_knowledge_base`.

3. STRICT CONSTRAINTS (OUT-OF-SCOPE):
   - You must NOT give medical advice, make diagnoses, prescribe medications, or comment on symptoms.
   - You must NOT answer personal questions about the doctors or staff.
   - If a patient asks for medical advice (e.g. "What should I take for a headache?"), or requests any action outside your list of tools, you MUST call `escalate_to_human_receptionist` immediately. Explain politely that you are routing them to a human receptionist who will contact them shortly.

4. SAFETY:
   - Always verify that the dates and times for scheduling/rescheduling are valid.
   - If a response from a database tool indicates an error, explain it nicely to the patient.
"""

def generate_agent_response(db: Session, phone_number: str, user_message: str) -> dict:
    """
    Processes the user's message, checks safety guardrails, queries the Gemini agent,
    runs tool calls against the database/RAG, and returns the response details.
    """
    logs = []
    rag_sources = []
    
    # 1. Screen incoming message for unacceptable content
    weird_flag, warning_reply = screen_incoming_message(user_message)
    if weird_flag:
        return {
            "reply": warning_reply,
            "patient_name": None,
            "escalated": False,
            "weird_flag": True,
            "logs": ["Safety Screen: Message blocked as weird or unacceptable."],
            "rag_sources": []
        }

    # 2. Get patient name if profile exists (for return meta)
    patient = crud.get_patient_by_phone(db, phone_number)
    patient_name = patient.name if patient else None

    # 3. Handle Gemini Agent response
    if not api_key:
        # MOCK MODE (if no API Key)
        logs.append("No Gemini API key found. Running in Rule-Based Mock Agent mode.")
        reply, escalated = handle_mock_agent(db, phone_number, user_message, logs, rag_sources)
        return {
            "reply": reply,
            "patient_name": patient_name,
            "escalated": escalated,
            "weird_flag": False,
            "logs": logs,
            "rag_sources": rag_sources
        }

    try:
        # Create Tool helper instance
        tools = ClinicTools(db, phone_number, logs, rag_sources)
        
        # Instantiate Gemini model with tools
        model = genai.GenerativeModel(
            model_name=gemini_model,
            tools=[
                tools.get_patient_details,
                tools.register_patient,
                tools.list_doctors,
                tools.book_appointment,
                tools.get_upcoming_appointments,
                tools.reschedule_appointment,
                tools.cancel_appointment,
                tools.get_billing_details,
                tools.pay_invoice,
                tools.search_clinic_knowledge_base,
                tools.escalate_to_human_receptionist
            ],
            system_instruction=SYSTEM_PROMPT
        )
        
        # Start a single-turn or multi-turn simulation chat
        # To simulate the conversation state context, we start a new chat history
        # We inject the patient's phone number as the initial context
        chat = model.start_chat(enable_automatic_function_calling=True)
        
        # Pre-populate context to let agent know who is talking
        logs.append("Initializing Agent chat session...")
        context_msg = f"Patient Phone Number: {phone_number}. Remember to query patient details first to greet them."
        chat.send_message(context_msg)
        
        # Send actual user message
        logs.append(f"User Message: {user_message}")
        response = chat.send_message(user_message)
        
        reply = response.text
        return {
            "reply": reply,
            "patient_name": patient_name or (crud.get_patient_by_phone(db, phone_number).name if crud.get_patient_by_phone(db, phone_number) else None),
            "escalated": tools.escalated,
            "weird_flag": False,
            "logs": logs,
            "rag_sources": rag_sources
        }
        
    except Exception as e:
        logs.append(f"Gemini API Error: {str(e)}")
        # Graceful fallback to Mock Agent
        logs.append("Falling back to Rule-Based Mock Agent...")
        reply, escalated = handle_mock_agent(db, phone_number, user_message, logs, rag_sources)
        return {
            "reply": f"🤖 (Fallback) {reply}",
            "patient_name": patient_name,
            "escalated": escalated,
            "weird_flag": False,
            "logs": logs,
            "rag_sources": rag_sources
        }

def handle_mock_agent(db: Session, phone_number: str, message: str, logs: list, rag_sources: list) -> tuple[str, bool]:
    """
    A smart rule-based mock agent that emulates clinic workflows, RAG lookups,
    and database API calls when Gemini API key is not present.
    """
    msg = message.strip().lower()
    patient = crud.get_patient_by_phone(db, phone_number)
    escalated = False

    # Check if patient exists
    if not patient:
        logs.append("Mock: Patient not found.")
        if "register" in msg or "name" in msg or "," in msg:
            # Try to parse registration (e.g. Sarah, sarah.jenkins@example.com, 1985-08-20)
            parts = [p.strip() for p in message.split(",")]
            if len(parts) >= 3:
                name, email, dob = parts[0], parts[1], parts[2]
                from app.schemas import PatientCreate
                p_new = crud.create_patient(db, PatientCreate(name=name, phone_number=phone_number, email=email, dob=dob))
                logs.append(f"Mock Tool Call: register_patient(name={name})")
                return f"Hello {p_new.name}, thank you for registering! I can now help you book appointments or answer billing queries. What can I do for you today?", False
            else:
                return "Welcome to Aura Wellness Clinic! I couldn't find an account matching your phone number. To register, please reply with your details in this format:\n\n*Name, Email, Date of Birth (YYYY-MM-DD)*\n\nExample: *John Doe, john@example.com, 1990-01-01*", False
        else:
            return "Welcome to Aura Wellness Clinic! It looks like you don't have an account registered with us yet. To create one, please reply with your:\n\n*Name, Email, Date of Birth (YYYY-MM-DD)*", False

    # Check for escalation triggers
    escalate_keywords = ["medical advice", "symptom", "pain", "headache", "fever", "prescribe", "medicine", "doctor's personal", "date", "marry"]
    for kw in escalate_keywords:
        if kw in msg:
            logs.append("Mock Tool Call: escalate_to_human_receptionist")
            escalated = True
            return f"I understand you have a personal request or medical query. I am escalating this conversation to our human receptionist who will contact you shortly. Please stay tuned.", True

    # Check for RAG FAQs first
    rag_results = rag_store.search_rag(db, message, limit=1)
    if rag_results and rag_results[0][1] > 0.3:  # Good match threshold
        doc, score = rag_results[0]
        logs.append(f"Mock RAG Match: {doc.title} (Score: {score:.2f})")
        rag_sources.append(f"{doc.title} (Category: {doc.category})")
        return f"Regarding your query: {doc.content}\n\nIs there anything else I can assist you with?", False

    # Appointment queries
    if "book" in msg or "schedule" in msg or "appointment" in msg:
        doctors = crud.get_doctors(db)
        if "doctor" in msg or "list" in msg:
            doc_list = "\n".join([f"- ID {d.id}: {d.name} ({d.specialty}) - Fee: ${d.consultation_fee} (Available: {d.available_hours})" for d in doctors])
            return f"Here are our available doctors:\n{doc_list}\n\nTo book, please tell me the Doctor's ID, and your preferred date & time (YYYY-MM-DD HH:MM).", False
        
        # Try to parse book details: e.g. "book 1 2026-06-25 10:00 checkup"
        try:
            tokens = msg.split()
            # Look for doctor id
            doc_id = None
            date_time = None
            for t in tokens:
                if t.isdigit() and int(t) in [d.id for d in doctors]:
                    doc_id = int(t)
            # Find date time YYYY-MM-DD
            import re
            date_match = re.search(r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}', message)
            if date_match:
                date_time = date_match.group(0)
            
            if doc_id and date_time:
                from app.schemas import AppointmentCreate
                appt_data = AppointmentCreate(patient_id=patient.id, doctor_id=doc_id, date_time=date_time, reason="Web Widget Reservation")
                appt = crud.create_appointment(db, appt_data)
                doc = crud.get_doctor(db, doc_id)
                logs.append(f"Mock Tool Call: book_appointment(doctor={doc_id})")
                return f"Success! I have booked your appointment with {doc.name} for {date_time}. Your appointment ID is {appt.id}.", False
        except Exception as e:
            logs.append(f"Mock Booking Parse Error: {str(e)}")

        return f"Hi {patient.name}, I can help you schedule, reschedule, or cancel appointments. To list doctors, say 'list doctors'. To book, specify the Doctor's ID and preferred date/time.", False

    # Reschedule/Cancel queries
    if "reschedule" in msg or "change" in msg:
        appts = crud.get_patient_appointments(db, patient.id)
        active = [a for a in appts if a.status in ["Scheduled", "Rescheduled"]]
        if not active:
            return f"Hi {patient.name}, you do not have any active appointments to reschedule.", False
        
        # Simple extraction
        # e.g. reschedule 1 to 2026-06-26 11:00
        import re
        appt_id = None
        for a in active:
            if str(a.id) in msg:
                appt_id = a.id
        date_match = re.search(r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}', message)
        
        if appt_id and date_match:
            new_time = date_match.group(0)
            crud.reschedule_appointment(db, appt_id, new_time)
            logs.append(f"Mock Tool Call: reschedule_appointment(id={appt_id})")
            return f"Great! Your appointment (ID: {appt_id}) has been rescheduled to {new_time}.", False

        appt_list = "\n".join([f"- ID {a.id}: with {a.doctor.name} on {a.date_time}" for a in active])
        return f"Which appointment would you like to reschedule?\n{appt_list}\n\nPlease respond with: 'reschedule [Appointment ID] to [YYYY-MM-DD HH:MM]'", False

    if "cancel" in msg:
        appts = crud.get_patient_appointments(db, patient.id)
        active = [a for a in appts if a.status in ["Scheduled", "Rescheduled"]]
        if not active:
            return f"Hi {patient.name}, you do not have any active appointments to cancel.", False
        
        for a in active:
            if str(a.id) in msg:
                crud.cancel_appointment(db, a.id)
                logs.append(f"Mock Tool Call: cancel_appointment(id={a.id})")
                return f"Your appointment (ID: {a.id}) with {a.doctor.name} has been successfully cancelled.", False
                
        appt_list = "\n".join([f"- ID {a.id}: with {a.doctor.name} on {a.date_time}" for a in active])
        return f"Which appointment would you like to cancel?\n{appt_list}\n\nPlease respond with: 'cancel [Appointment ID]'", False

    # Billing/Payment queries
    if "bill" in msg or "invoice" in msg or "pay" in msg or "charge" in msg or "cost" in msg:
        bills = crud.get_patient_billing(db, patient.id)
        pending = [b for b in bills if b.status == "Pending"]
        
        if "pay" in msg:
            # Pay bill if specified
            for b in pending:
                if str(b.id) in msg or "all" in msg:
                    crud.pay_invoice(db, b.id)
                    logs.append(f"Mock Tool Call: pay_invoice(id={b.id})")
                    return f"Thank you! Your payment of ${b.amount:.2f} for Invoice #{b.id} has been processed successfully.", False
            
            if pending:
                bill_list = "\n".join([f"- Invoice #{b.id}: ${b.amount:.2f} (Due: {b.due_date}) - {b.details}" for b in pending])
                return f"You have the following unpaid invoice(s):\n{bill_list}\n\nTo pay, please reply with 'pay [Invoice ID]'.", False
        
        bill_list = []
        for b in bills:
            status_emoji = "⏳ Pending" if b.status == "Pending" else "✅ Paid"
            bill_list.append(f"- Invoice #{b.id}: ${b.amount:.2f} ({status_emoji}, Due: {b.due_date}) - {b.details}")
            
        bill_str = "\n".join(bill_list) if bill_list else "No bills found on record."
        return f"Here is your billing statement:\n{bill_str}\n\nTo pay any pending bills, say 'pay [Invoice ID]'.", False

    # Fallback default conversational greeting
    return f"Hi {patient.name}! I am Aria from Aura Wellness Clinic. I can assist you with booking/modifying appointments, checking your bills, or answering basic clinic policies. How can I help you today?", False
