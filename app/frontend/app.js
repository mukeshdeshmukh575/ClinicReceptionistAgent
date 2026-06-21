let currentTab = 'doctors';
let activePhoneNumber = "+919876543210";

// Map to convert database data into clean tables
const tableRenderers = {
    doctors: (data) => {
        if (!data || data.length === 0) return '<tr><td colspan="4">No doctors available.</td></tr>';
        let html = `
            <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Specialty</th>
                <th>Available Hours</th>
                <th>Fee</th>
            </tr>
        `;
        data.forEach(d => {
            html += `
                <tr>
                    <td><strong>${d.id}</strong></td>
                    <td>${d.name}</td>
                    <td><span class="status-pill status-rescheduled">${d.specialty}</span></td>
                    <td>${d.available_hours}</td>
                    <td><strong>$${d.consultation_fee}</strong></td>
                </tr>
            `;
        });
        return html;
    },
    patients: (data) => {
        if (!data || data.length === 0) return '<tr><td colspan="5">No patients registered.</td></tr>';
        let html = `
            <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Phone Number</th>
                <th>Email</th>
                <th>Date of Birth</th>
            </tr>
        `;
        // Check if data is array or single object
        const patientsList = Array.isArray(data) ? data : [data];
        patientsList.forEach(p => {
            html += `
                <tr>
                    <td><strong>${p.id}</strong></td>
                    <td>${p.name}</td>
                    <td>${p.phone_number}</td>
                    <td>${p.email || 'N/A'}</td>
                    <td>${p.dob || 'N/A'}</td>
                </tr>
            `;
        });
        return html;
    },
    appointments: (data) => {
        if (!data || data.length === 0) return '<tr><td colspan="6">No appointments on record.</td></tr>';
        let html = `
            <tr>
                <th>ID</th>
                <th>Patient ID</th>
                <th>Doctor ID</th>
                <th>Date & Time</th>
                <th>Status</th>
                <th>Reason</th>
            </tr>
        `;
        data.forEach(a => {
            let statusClass = 'status-scheduled';
            if (a.status === 'Rescheduled') statusClass = 'status-rescheduled';
            if (a.status === 'Cancelled') statusClass = 'status-cancelled';
            
            html += `
                <tr>
                    <td><strong>${a.id}</strong></td>
                    <td>Patient #${a.patient_id}</td>
                    <td>Doctor #${a.doctor_id}</td>
                    <td>${a.date_time}</td>
                    <td><span class="status-pill ${statusClass}">${a.status}</span></td>
                    <td>${a.reason || 'N/A'}</td>
                </tr>
            `;
        });
        return html;
    },
    billing: (data) => {
        if (!data || data.length === 0) return '<tr><td colspan="6">No bills on record.</td></tr>';
        let html = `
            <tr>
                <th>Invoice ID</th>
                <th>Patient ID</th>
                <th>Amount</th>
                <th>Status</th>
                <th>Due Date</th>
                <th>Description</th>
            </tr>
        `;
        data.forEach(b => {
            let statusClass = b.status === 'Paid' ? 'status-paid' : 'status-pending';
            html += `
                <tr>
                    <td><strong>#${b.id}</strong></td>
                    <td>Patient #${b.patient_id}</td>
                    <td><strong>$${b.amount.toFixed(2)}</strong></td>
                    <td><span class="status-pill ${statusClass}">${b.status}</span></td>
                    <td>${b.due_date}</td>
                    <td>${b.details || 'N/A'}</td>
                </tr>
            `;
        });
        return html;
    }
};

// Initialize Dashboard
document.addEventListener('DOMContentLoaded', () => {
    fetchCurrentTable();
    updateIdentityCard();
});

// Switch DB Tabs
function switchDbTab(tabName) {
    currentTab = tabName;
    
    // Update active tab class
    const tabs = document.querySelectorAll('.db-tab');
    tabs.forEach(tab => {
        if (tab.innerText.toLowerCase() === tabName || (tabName === 'billing' && tab.innerText.toLowerCase() === 'invoices')) {
            tab.classList.add('active');
        } else {
            tab.classList.remove('active');
        }
    });
    
    fetchCurrentTable();
}

// Fetch DB details
async function fetchCurrentTable() {
    const tableEl = document.getElementById('db-table');
    tableEl.innerHTML = '<tr><td style="text-align: center; padding: 2rem;">Loading data...</td></tr>';
    
    let endpoint = '/api/doctors';
    
    if (currentTab === 'patients') {
        // Since backend might only support reading single patient by phone,
        // we fetch the details of the active patient to display.
        endpoint = `/api/patients/by-phone/${encodeURIComponent(activePhoneNumber)}`;
    } else if (currentTab === 'appointments') {
        // Fetch active patient profile first to get patient ID
        try {
            const pRes = await fetch(`/api/patients/by-phone/${encodeURIComponent(activePhoneNumber)}`);
            if (pRes.ok) {
                const patient = await pRes.json();
                endpoint = `/api/appointments/patient/${patient.id}`;
            } else {
                tableEl.innerHTML = '<tr><td style="text-align: center; padding: 2rem; color: #f87171;">Unregistered patient. No appointment record.</td></tr>';
                return;
            }
        } catch (err) {
            console.error(err);
            tableEl.innerHTML = '<tr><td style="text-align: center; padding: 2rem; color: #f87171;">Error resolving patient context.</td></tr>';
            return;
        }
    } else if (currentTab === 'billing') {
        try {
            const pRes = await fetch(`/api/patients/by-phone/${encodeURIComponent(activePhoneNumber)}`);
            if (pRes.ok) {
                const patient = await pRes.json();
                endpoint = `/api/billing/patient/${patient.id}`;
            } else {
                tableEl.innerHTML = '<tr><td style="text-align: center; padding: 2rem; color: #f87171;">Unregistered patient. No invoice records.</td></tr>';
                return;
            }
        } catch (err) {
            console.error(err);
            tableEl.innerHTML = '<tr><td style="text-align: center; padding: 2rem; color: #f87171;">Error resolving patient context.</td></tr>';
            return;
        }
    }

    try {
        const response = await fetch(endpoint);
        if (response.ok) {
            const data = await response.json();
            tableEl.innerHTML = tableRenderers[currentTab](data);
        } else {
            if (currentTab === 'patients') {
                tableEl.innerHTML = '<tr><td style="text-align: center; padding: 2rem; color: #fbbf24;"><i class="fa-solid fa-triangle-exclamation"></i> Patient is not registered yet.</td></tr>';
            } else {
                tableEl.innerHTML = '<tr><td style="text-align: center; padding: 2rem; color: #f87171;">Failed to load data.</td></tr>';
            }
        }
    } catch (err) {
        console.error("API Fetch Error: ", err);
        tableEl.innerHTML = '<tr><td style="text-align: center; padding: 2rem; color: #f87171;">Error connecting to API.</td></tr>';
    }
}

// Phone selector change callback
function onPatientSelectChange() {
    const selector = document.getElementById('patient-selector');
    activePhoneNumber = selector.value;
    
    // Clear chat thread except initial greeting
    const chatArea = document.getElementById('chat-messages');
    chatArea.innerHTML = `
        <div class="message-bubble message-incoming">
            Hi! I am Aria, your virtual receptionist for Aura Wellness Clinic. How can I help you today?
            <div class="message-time">12:00 PM</div>
        </div>
    `;

    // Clear diagnostics
    document.getElementById('escalation-banner').style.display = 'none';
    document.getElementById('safety-banner').style.display = 'none';
    document.getElementById('tool-logs').innerText = 'System re-initialized...';
    document.getElementById('rag-sources').innerHTML = '<div style="font-size: 0.8rem; color: var(--text-secondary); italic;">No RAG fetches triggered.</div>';

    // Update identities and tables
    updateIdentityCard();
    fetchCurrentTable();
}

// Update Active Patient Metadata Card
async function updateIdentityCard() {
    const phoneEl = document.getElementById('active-phone-number');
    const nameEl = document.getElementById('active-patient-name');
    
    phoneEl.innerText = activePhoneNumber;
    nameEl.innerText = "Resolving...";
    
    try {
        const response = await fetch(`/api/patients/by-phone/${encodeURIComponent(activePhoneNumber)}`);
        if (response.ok) {
            const data = await response.json();
            nameEl.innerText = data.name;
        } else {
            nameEl.innerText = "Unregistered Patient";
        }
    } catch (e) {
        nameEl.innerText = "Unknown/Error";
    }
}

// Send user message through simulator
async function sendMessage() {
    const inputEl = document.getElementById('chat-input');
    const message = inputEl.value.trim();
    if (!message) return;
    
    inputEl.value = '';
    
    // 1. Render user message in chat
    renderMessage(message, 'outgoing');
    
    // 2. Render Typing indicator
    const typingId = renderTypingIndicator();
    
    try {
        // Send request to webhook simulator
        const response = await fetch('/api/chat/simulate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                phone_number: activePhoneNumber,
                message: message
            })
        });

        // Remove typing indicator
        document.getElementById(typingId)?.remove();

        if (response.ok) {
            const result = await response.json();
            
            // 3. Render Agent Response
            renderMessage(result.reply, 'incoming');
            
            // 4. Update Logs & Diagnostics
            updateDiagnostics(result);
            
            // 5. Automatically refresh the database view to reflect modifications!
            fetchCurrentTable();
            updateIdentityCard();
        } else {
            renderMessage("Sorry, I encountered a communication error with my backend. Please try again.", 'incoming');
        }
    } catch (err) {
        console.error("Chat Post Error:", err);
        document.getElementById(typingId)?.remove();
        renderMessage("Connection failed. Please ensure the FastAPI server is running.", 'incoming');
    }
}

// Helper: Format Message Time
function getFormattedTime() {
    const now = new Date();
    return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

// Render message bubble
function renderMessage(text, direction) {
    const chatArea = document.getElementById('chat-messages');
    const bubble = document.createElement('div');
    bubble.className = `message-bubble message-${direction}`;
    
    // Preserve formatting with pre-wrap
    bubble.style.whiteSpace = 'pre-wrap';
    bubble.innerHTML = text.replace(/\n/g, '<br>') + `<div class="message-time">${getFormattedTime()}</div>`;
    
    chatArea.appendChild(bubble);
    chatArea.scrollTop = chatArea.scrollHeight;
}

// Render Typing indicator bubble
function renderTypingIndicator() {
    const chatArea = document.getElementById('chat-messages');
    const indicator = document.createElement('div');
    const id = 'typing-' + Date.now();
    
    indicator.id = id;
    indicator.className = 'message-bubble message-incoming';
    indicator.innerHTML = '<span style="color: var(--text-secondary); italic;">Aria is typing...</span>';
    
    chatArea.appendChild(indicator);
    chatArea.scrollTop = chatArea.scrollHeight;
    return id;
}

// Update log sections, RAG items, banners
function updateDiagnostics(data) {
    // 1. Tool Logs
    const logBox = document.getElementById('tool-logs');
    if (data.logs && data.logs.length > 0) {
        logBox.innerText = data.logs.join('\n');
    } else {
        logBox.innerText = 'No system logs recorded for this turn.';
    }
    
    // 2. RAG sources
    const ragBox = document.getElementById('rag-sources');
    if (data.rag_sources && data.rag_sources.length > 0) {
        ragBox.innerHTML = '';
        data.rag_sources.forEach(src => {
            const item = document.createElement('div');
            item.className = 'rag-source-item';
            item.innerHTML = `<i class="fa-solid fa-check"></i> ${src}`;
            ragBox.appendChild(item);
        });
    } else {
        ragBox.innerHTML = '<div style="font-size: 0.8rem; color: var(--text-secondary); italic;">No RAG fetches triggered by current message.</div>';
    }
    
    // 3. Escalation banner
    const escBanner = document.getElementById('escalation-banner');
    if (data.escalated) {
        escBanner.style.display = 'block';
        document.getElementById('escalation-reason').innerText = `Reason: Query out of scope. Handed over to human receptionist.`;
    } else {
        escBanner.style.display = 'none';
    }

    // 4. Weird filter banner
    const safetyBanner = document.getElementById('safety-banner');
    if (data.weird_flag) {
        safetyBanner.style.display = 'block';
    } else {
        safetyBanner.style.display = 'none';
    }
}

// Keyboard listener
function handleInputKeydown(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}
