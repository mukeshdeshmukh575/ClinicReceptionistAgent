(function() {
    // 1. Inject Stylesheets dynamically
    const fontLink1 = document.createElement('link');
    fontLink1.rel = 'stylesheet';
    fontLink1.href = 'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;500;600;700;800&display=swap';
    document.head.appendChild(fontLink1);

    const iconLink = document.createElement('link');
    iconLink.rel = 'stylesheet';
    iconLink.href = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css';
    document.head.appendChild(iconLink);

    // 2. Inject CSS Styles for the Widget
    const style = document.createElement('style');
    style.innerHTML = `
        :root {
            --widget-bg: rgba(15, 23, 42, 0.9);
            --widget-border: rgba(255, 255, 255, 0.1);
            --widget-text-primary: #f8fafc;
            --widget-text-secondary: #94a3b8;
            --widget-cyan: #06b6d4;
            --widget-green: #10b981;
            --widget-purple: #6366f1;
            --widget-red: #ef4444;
            --widget-glow-cyan: 0 0 15px rgba(6, 182, 212, 0.4);
            --widget-glow-purple: 0 0 15px rgba(99, 102, 241, 0.4);
        }

        /* Floating Chat Button */
        #aura-chat-bubble {
            position: fixed;
            bottom: 30px;
            right: 30px;
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: linear-gradient(135deg, var(--widget-cyan) 0%, var(--widget-purple) 100%);
            box-shadow: var(--widget-glow-cyan);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 99999;
            transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            animation: aura-pulse 2s infinite alternate;
        }

        #aura-chat-bubble:hover {
            transform: scale(1.1) rotate(5deg);
            box-shadow: 0 0 25px rgba(6, 182, 212, 0.7);
        }

        #aura-chat-bubble i {
            color: white;
            font-size: 1.6rem;
            transition: all 0.3s ease;
        }

        @keyframes aura-pulse {
            from { box-shadow: 0 0 12px rgba(6, 182, 212, 0.3); }
            to { box-shadow: 0 0 22px rgba(99, 102, 241, 0.6); }
        }

        /* Chat Widget Container */
        #aura-chat-widget {
            position: fixed;
            bottom: 105px;
            right: 30px;
            width: 380px;
            height: 580px;
            background: var(--widget-bg);
            backdrop-filter: blur(25px);
            border: 1px solid var(--widget-border);
            border-radius: 20px;
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.5);
            z-index: 99998;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            font-family: 'Inter', sans-serif;
            transform: translateY(30px) scale(0.95);
            opacity: 0;
            pointer-events: none;
            transition: all 0.3s cubic-bezier(0.165, 0.84, 0.44, 1);
        }

        #aura-chat-widget.active {
            transform: translateY(0) scale(1);
            opacity: 1;
            pointer-events: auto;
        }

        /* Header */
        .aura-header {
            background: rgba(15, 23, 42, 0.6);
            border-bottom: 1px solid var(--widget-border);
            padding: 1rem 1.25rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .aura-header-left {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .aura-avatar {
            width: 38px;
            height: 38px;
            border-radius: 50%;
            background: linear-gradient(135deg, #22d3ee 0%, #818cf8 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            color: #0f172a;
            font-family: 'Outfit', sans-serif;
        }

        .aura-header-info {
            display: flex;
            flex-direction: column;
        }

        .aura-header-info h4 {
            color: var(--widget-text-primary);
            font-family: 'Outfit', sans-serif;
            font-size: 0.95rem;
            font-weight: 600;
            margin: 0;
        }

        .aura-header-info span {
            font-size: 0.72rem;
            color: var(--widget-green);
            display: flex;
            align-items: center;
            gap: 0.25rem;
            margin-top: 0.1rem;
        }

        .aura-header-info span::before {
            content: '';
            display: inline-block;
            width: 6px;
            height: 6px;
            background-color: var(--widget-green);
            border-radius: 50%;
        }

        .aura-close-btn {
            background: transparent;
            border: none;
            color: var(--widget-text-secondary);
            font-size: 1.1rem;
            cursor: pointer;
            transition: color 0.2s;
            padding: 0.25rem;
        }

        .aura-close-btn:hover {
            color: var(--widget-text-primary);
        }

        /* Identity Overlay / Phone Settings */
        .aura-identity-panel {
            background: rgba(99, 102, 241, 0.08);
            border-bottom: 1px solid rgba(99, 102, 241, 0.2);
            padding: 0.65rem 1rem;
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
            font-size: 0.78rem;
        }

        .aura-identity-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.5rem;
        }

        .aura-identity-input {
            flex-grow: 1;
            background: rgba(0, 0, 0, 0.4);
            border: 1px solid var(--widget-border);
            border-radius: 6px;
            padding: 0.35rem 0.6rem;
            color: white;
            font-size: 0.78rem;
            outline: none;
        }

        .aura-identity-input::placeholder {
            color: #64748b;
        }

        .aura-identity-btn {
            background: var(--widget-purple);
            border: none;
            color: white;
            padding: 0.35rem 0.75rem;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 500;
            transition: filter 0.2s;
        }

        .aura-identity-btn:hover {
            filter: brightness(1.1);
        }

        .aura-identity-status {
            display: flex;
            align-items: center;
            justify-content: space-between;
            color: var(--widget-text-secondary);
        }

        /* Message Area */
        .aura-chat-messages {
            flex-grow: 1;
            padding: 1.25rem;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 0.85rem;
            background: rgba(15, 23, 42, 0.3);
        }

        .aura-bubble {
            max-width: 82%;
            padding: 0.65rem 0.85rem;
            border-radius: 14px;
            font-size: 0.85rem;
            line-height: 1.45;
            position: relative;
            animation: aura-slide-up 0.25s ease-out;
        }

        @keyframes aura-slide-up {
            from { transform: translateY(8px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }

        .aura-bubble-incoming {
            background: rgba(30, 41, 59, 0.8);
            border: 1px solid var(--widget-border);
            color: var(--widget-text-primary);
            align-self: flex-start;
            border-top-left-radius: 3px;
        }

        .aura-bubble-outgoing {
            background: linear-gradient(135deg, rgba(6, 182, 212, 0.25) 0%, rgba(99, 102, 241, 0.25) 100%);
            border: 1px solid rgba(6, 182, 212, 0.3);
            color: var(--widget-text-primary);
            align-self: flex-end;
            border-top-right-radius: 3px;
        }

        .aura-bubble-time {
            font-size: 0.65rem;
            color: #64748b;
            text-align: right;
            margin-top: 0.25rem;
        }

        /* Input Area */
        .aura-input-bar {
            padding: 0.85rem 1rem;
            background: rgba(15, 23, 42, 0.7);
            border-top: 1px solid var(--widget-border);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .aura-input-bar input {
            flex-grow: 1;
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid var(--widget-border);
            outline: none;
            color: white;
            padding: 0.6rem 1rem;
            border-radius: 25px;
            font-size: 0.85rem;
            transition: border-color 0.2s;
        }

        .aura-input-bar input:focus {
            border-color: var(--widget-cyan);
        }

        .aura-input-bar button {
            background: linear-gradient(135deg, var(--widget-cyan) 0%, var(--widget-purple) 100%);
            color: white;
            border: none;
            outline: none;
            width: 36px;
            height: 36px;
            border-radius: 50%;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s ease;
        }

        .aura-input-bar button:hover {
            transform: scale(1.05);
            box-shadow: 0 0 10px rgba(6, 182, 212, 0.4);
        }

        /* Alert Banners inside widget */
        .aura-alert {
            background: rgba(239, 68, 68, 0.15);
            border: 1px solid rgba(239, 68, 68, 0.3);
            border-radius: 8px;
            padding: 0.5rem;
            font-size: 0.75rem;
            color: #f87171;
            text-align: center;
            margin-bottom: 0.5rem;
        }

        .aura-alert-warn {
            background: rgba(245, 158, 11, 0.15);
            border: 1px solid rgba(245, 158, 11, 0.3);
            color: #fbbf24;
        }
    `;
    document.head.appendChild(style);

    // 3. Create DOM Elements
    const chatBubble = document.createElement('div');
    chatBubble.id = 'aura-chat-bubble';
    chatBubble.innerHTML = '<i class="fa-solid fa-comments"></i>';
    document.body.appendChild(chatBubble);

    const chatWidget = document.createElement('div');
    chatWidget.id = 'aura-chat-widget';
    chatWidget.innerHTML = `
        <!-- Header -->
        <div class="aura-header">
            <div class="aura-header-left">
                <div class="aura-avatar">A</div>
                <div class="aura-header-info">
                    <h4>Aria (Virtual Assistant)</h4>
                    <span>Aura Wellness Clinic</span>
                </div>
            </div>
            <button class="aura-close-btn" id="aura-close-btn"><i class="fa-solid fa-xmark"></i></button>
        </div>

        <!-- Identity Settings -->
        <div class="aura-identity-panel" id="aura-identity-panel">
            <!-- Filled dynamically based on state -->
        </div>

        <!-- Messages thread -->
        <div class="aura-chat-messages" id="aura-chat-messages">
            <div class="aura-bubble aura-bubble-incoming">
                Hi! I am Aria, your virtual assistant for Aura Wellness Clinic. Feel free to ask me about doctor specialties, hours, policies, or manage your bookings.
                <div class="aura-bubble-time">${getCurrentTime()}</div>
            </div>
        </div>

        <!-- Input Bar -->
        <div class="aura-input-bar">
            <input type="text" id="aura-chat-input" placeholder="Ask something..." onkeydown="if(event.key==='Enter') document.getElementById('aura-send-btn').click()">
            <button id="aura-send-btn"><i class="fa-solid fa-paper-plane"></i></button>
        </div>
    `;
    document.body.appendChild(chatWidget);

    // 4. State Management
    let currentPhone = localStorage.getItem('aura_chat_phone') || "";
    const apiBaseUrl = document.currentScript ? document.currentScript.getAttribute('data-api-url') || "" : "";

    // DOM References
    const chatBubbleEl = document.getElementById('aura-chat-bubble');
    const chatWidgetEl = document.getElementById('aura-chat-widget');
    const closeBtnEl = document.getElementById('aura-close-btn');
    const messagesEl = document.getElementById('aura-chat-messages');
    const inputEl = document.getElementById('aura-chat-input');
    const sendBtnEl = document.getElementById('aura-send-btn');
    const identityPanelEl = document.getElementById('aura-identity-panel');

    // 5. Initialize Identity Pane
    renderIdentityPanel();

    // Toggle Chat visibility
    chatBubbleEl.addEventListener('click', () => {
        chatWidgetEl.classList.toggle('active');
        if (chatWidgetEl.classList.contains('active')) {
            chatBubbleEl.style.display = 'none';
            inputEl.focus();
            scrollToBottom();
        }
    });

    closeBtnEl.addEventListener('click', () => {
        chatWidgetEl.classList.remove('active');
        chatBubbleEl.style.display = 'flex';
    });

    // Send handler
    sendBtnEl.addEventListener('click', () => {
        const text = inputEl.value.trim();
        if (!text) return;

        // Append outgoing message
        appendMessage(text, 'outgoing');
        inputEl.value = '';

        // API Call
        sendToAgent(text);
    });

    // Helper functions
    function getCurrentTime() {
        const d = new Date();
        let hours = d.getHours();
        let minutes = d.getMinutes();
        const ampm = hours >= 12 ? 'PM' : 'AM';
        hours = hours % 12;
        hours = hours ? hours : 12;
        minutes = minutes < 10 ? '0' + minutes : minutes;
        return hours + ':' + minutes + ' ' + ampm;
    }

    function renderIdentityPanel() {
        if (currentPhone) {
            identityPanelEl.innerHTML = `
                <div class="aura-identity-status">
                    <span><i class="fa-solid fa-circle-check" style="color:var(--widget-green)"></i> Account: <strong>${currentPhone}</strong></span>
                    <a href="#" id="aura-logout-link" style="color:#6366f1; text-decoration:none; font-weight:600;">Sign Out</a>
                </div>
            `;
            document.getElementById('aura-logout-link').addEventListener('click', (e) => {
                e.preventDefault();
                currentPhone = "";
                localStorage.removeItem('aura_chat_phone');
                renderIdentityPanel();
            });
        } else {
            identityPanelEl.innerHTML = `
                <div class="aura-identity-row">
                    <input type="text" id="aura-phone-field" class="aura-identity-input" placeholder="Enter phone number to link profile...">
                    <button id="aura-link-btn" class="aura-identity-btn">Link Account</button>
                </div>
            `;
            document.getElementById('aura-link-btn').addEventListener('click', () => {
                const phoneField = document.getElementById('aura-phone-field');
                const val = phoneField.value.trim();
                if (val) {
                    currentPhone = val;
                    localStorage.setItem('aura_chat_phone', val);
                    renderIdentityPanel();
                    appendMessage(`Phone number updated to: ${val}`, 'incoming');
                }
            });
        }
    }

    function appendMessage(text, type, timeStr = null) {
        const time = timeStr || getCurrentTime();
        const bubble = document.createElement('div');
        bubble.className = `aura-bubble aura-bubble-${type}`;
        bubble.innerHTML = `
            ${text.replace(/\n/g, '<br>')}
            <div class="aura-bubble-time">${time}</div>
        `;
        messagesEl.appendChild(bubble);
        scrollToBottom();
    }

    function scrollToBottom() {
        messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    async function sendToAgent(msgText) {
        // Typing indicator
        const typingIndicator = document.createElement('div');
        typingIndicator.id = 'aura-typing';
        typingIndicator.className = 'aura-bubble aura-bubble-incoming';
        typingIndicator.innerHTML = '<i class="fa-solid fa-ellipsis fa-bounce"></i> typing...';
        messagesEl.appendChild(typingIndicator);
        scrollToBottom();

        try {
            // If phone number is empty, default to '+0000000000' (treated as unregistered patient by the system)
            const phone = currentPhone || "+0000000000";

            const res = await fetch(`${apiBaseUrl}/api/chat/simulate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ phone_number: phone, message: msgText })
            });

            const data = await res.json();
            
            // Remove typing indicator
            const indicator = document.getElementById('aura-typing');
            if (indicator) indicator.remove();

            if (data.weird_flag) {
                // Warning safety screen triggers
                const alertDiv = document.createElement('div');
                alertDiv.className = 'aura-alert aura-alert-warn';
                alertDiv.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i> Out-of-bounds message flagged.';
                messagesEl.appendChild(alertDiv);
            }

            if (data.escalated) {
                // Human escalation
                const alertDiv = document.createElement('div');
                alertDiv.className = 'aura-alert';
                alertDiv.innerHTML = '<i class="fa-solid fa-headset"></i> Human escalation triggered.';
                messagesEl.appendChild(alertDiv);
            }

            appendMessage(data.reply, 'incoming');

        } catch (err) {
            console.error("Widget API request failed:", err);
            const indicator = document.getElementById('aura-typing');
            if (indicator) indicator.remove();
            appendMessage("Sorry, I am having trouble connecting to the clinic server. Please check your connection and try again.", 'incoming');
        }
    }
})();
