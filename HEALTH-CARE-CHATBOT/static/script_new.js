/* ========================================
   MEDICHAT - MODERN SCRIPT WITH Q&A
   ======================================== */

// ========== GLOBAL VARIABLES ==========

let recognition;
let isListening = false;
let voiceEnabled = localStorage.getItem('voiceEnabled') === 'true';
let chatHistory = [];
let currentDiagnosis = null;

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
const synth = window.speechSynthesis;

// ========== MEDICAL TERMS DATABASE ==========

const MEDICAL_TERMS = [
    'fever', 'cough', 'headache', 'body ache', 'fatigue', 'cold', 'nausea', 'diarrhea',
    'congestion', 'sore throat', 'rash', 'swelling', 'itching', 'chills', 'dengue',
    'malaria', 'diabetes', 'hypertension', 'cholera', 'pneumonia', 'tuberculosis',
    'typhoid', 'asthma', 'bronchitis', 'pneumonitis', 'cardiac', 'heart', 'stroke',
    'anxiety', 'depression', 'vertigo', 'acne', 'ulcers', 'hemorrhoids', 'arthritis',
    'psoriasis', 'impetigo', 'fungal', 'allergy', 'jaundice', 'precaution', 'symptom',
    'disease', 'medication', 'treatment', 'doctor', 'hospital', 'pharmacy'
];

// ========== INITIALIZATION ==========

document.addEventListener('DOMContentLoaded', function() {
    initializeVoiceRecognition();
    loadChatHistory();
    setupEventListeners();
    updateVoiceToggleUI();
});

function initializeVoiceRecognition() {
    if (!SpeechRecognition) {
        console.warn('Speech Recognition not supported');
        document.getElementById('voiceInputBtn').style.display = 'none';
        return;
    }

    recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.language = 'en-US';

    recognition.onstart = () => {
        isListening = true;
        document.getElementById('voiceInputBtn').classList.add('active');
        showVoiceFeedback();
    };

    recognition.onresult = (event) => {
        let interimTranscript = '';
        let finalTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcript = event.results[i].transcript;
            if (event.results[i].isFinal) {
                finalTranscript += transcript;
            } else {
                interimTranscript += transcript;
            }
        }

        const recognized = document.getElementById('recognizedText');
        if (interimTranscript) {
            recognized.textContent = '📝 ' + interimTranscript;
        } else if (finalTranscript) {
            recognized.textContent = '✅ ' + finalTranscript;
        }

        if (finalTranscript) {
            document.getElementById('symptomInput').value = finalTranscript;
        }
    };

    recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        document.getElementById('recognizedText').textContent = '❌ Error: ' + event.error;
    };

    recognition.onend = () => {
        isListening = false;
        document.getElementById('voiceInputBtn').classList.remove('active');
        hideVoiceFeedback();
    };
}

function setupEventListeners() {
    const input = document.getElementById('symptomInput');
    const sendBtn = document.getElementById('sendBtn');
    const voiceBtn = document.getElementById('voiceInputBtn');
    const voiceToggle = document.getElementById('voiceAssistantToggle');
    const clearBtn = document.getElementById('clearHistoryBtn');
    const diagnosisTab = document.getElementById('diagnosisTab');
    const healthTipsTab = document.getElementById('healthTipsTab');
    const historyBtn = document.getElementById('historyBtn');

    // Send message on Enter key
    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && input.value.trim()) {
            sendMessage();
        }
    });

    sendBtn.addEventListener('click', sendMessage);
    voiceBtn.addEventListener('click', toggleVoiceInput);
    voiceToggle.addEventListener('click', toggleVoiceAssistant);
    clearBtn.addEventListener('click', clearHistory);
    diagnosisTab.addEventListener('click', () => setActiveTab('diagnosis'));
    healthTipsTab.addEventListener('click', () => setActiveTab('health-tips'));
    historyBtn.addEventListener('click', () => setActiveTab('history'));
}

// ========== VOICE FUNCTIONS ==========

function toggleVoiceInput() {
    if (!recognition) return;

    if (isListening) {
        recognition.stop();
    } else {
        recognition.start();
    }
}

function toggleVoiceAssistant() {
    voiceEnabled = !voiceEnabled;
    localStorage.setItem('voiceEnabled', voiceEnabled);
    updateVoiceToggleUI();
}

function updateVoiceToggleUI() {
    const btn = document.getElementById('voiceAssistantToggle');
    btn.classList.toggle('active', voiceEnabled);
    btn.textContent = voiceEnabled ? '🔊' : '🔇';
}

function showVoiceFeedback() {
    document.getElementById('voiceFeedback').style.display = 'flex';
}

function hideVoiceFeedback() {
    document.getElementById('voiceFeedback').style.display = 'none';
}

function speakBot(text) {
    if (!voiceEnabled || !synth) return;

    synth.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.9;
    utterance.pitch = 1;
    utterance.volume = 1;
    synth.speak(utterance);
}

// ========== MESSAGE HANDLING ==========

function sendMessage() {
    const input = document.getElementById('symptomInput');
    const text = input.value.trim();

    if (!text) return;

    // Add user message to chat
    addMessage('user', text);
    input.value = '';

    // Determine if question or symptom check
    const isQuestion = text.includes('?') || 
                       text.toLowerCase().includes('how') ||
                       text.toLowerCase().includes('what') ||
                       text.toLowerCase().includes('when') ||
                       text.toLowerCase().includes('why') ||
                       text.toLowerCase().includes('tell');

    if (isQuestion) {
        handleHealthQA(text);
    } else {
        handleDiagnosis(text);
    }
}

function handleHealthQA(question) {
    const resultsPanel = document.getElementById('resultsPanel');

    fetch('/api/health_qa', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: question })
    })
    .then(response => response.json())
    .then(data => {
        addMessage('bot', data.answer);
        speakBot(data.answer);

        // Display in sidebar
        const resultHTML = `
            <div class="diagnosis-result">
                <div class="result-title">💡 Health Information</div>
                <div class="result-item">
                    <div class="result-value">${highlightMedicalTerms(data.answer)}</div>
                </div>
                <div class="action-buttons">
                    <button class="action-btn" onclick="copyResult('${data.answer.replace(/'/g, "\\'")}')">📋 Copy</button>
                    <button class="action-btn" onclick="speakBot('${data.answer.replace(/'/g, "\\'")}')">🔊 Read</button>
                </div>
            </div>
        `;
        resultsPanel.innerHTML = resultHTML;
    })
    .catch(error => {
        console.error('Error:', error);
        const errorMsg = 'Sorry, I could not answer that question. Please try rephrasing.';
        addMessage('bot', errorMsg);
        speakBot(errorMsg);
    });
}

function handleDiagnosis(input) {
    const resultsPanel = document.getElementById('resultsPanel');

    fetch('/api/diagnose', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symptoms: input })
    })
    .then(response => response.json())
    .then(data => {
        currentDiagnosis = data;

        if (data.disease) {
            addMessage('bot', `I detected: ${data.disease}`);
            speakBot(`I detected: ${data.disease}`);

            // Display diagnosis in sidebar
            const resultHTML = `
                <div class="diagnosis-result">
                    <div class="result-title">🏥 Diagnosis Result</div>
                    <div class="result-item">
                        <div class="result-label">Detected Disease</div>
                        <div class="result-value">${data.disease}</div>
                    </div>
                    <div class="result-item">
                        <div class="result-label">Confidence</div>
                        <div class="result-value">${data.confidence || 'N/A'}</div>
                    </div>
                    <div class="result-item">
                        <div class="result-label">Precautions</div>
                        <ul class="precaution-list">
                            ${(data.precautions || []).map(p => `<li>${p}</li>`).join('')}
                        </ul>
                    </div>
                    <div class="action-buttons">
                        <button class="action-btn" onclick="copyResult('${data.disease}')">📋 Copy</button>
                        <button class="action-btn" onclick="askFollowup()">❓ More Details</button>
                    </div>
                </div>
            `;
            resultsPanel.innerHTML = resultHTML;
        } else {
            const msg = 'Please describe your symptoms more clearly. Example: "I have fever and cough"';
            addMessage('bot', msg);
            speakBot(msg);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        const errorMsg = 'An error occurred during diagnosis. Please try again.';
        addMessage('bot', errorMsg);
    });
}

function askFollowup() {
    if (!currentDiagnosis) return;
    const resultsPanel = document.getElementById('resultsPanel');
    
    const followupHTML = `
        <div class="diagnosis-result">
            <div class="result-title">❓ Follow-up Questions</div>
            <div class="result-item">
                <button class="action-btn" onclick="setInput('More severe symptoms')">More Severe?</button>
                <button class="action-btn" onclick="setInput('Duration of disease')">How Long?</button>
            </div>
        </div>
    `;
    resultsPanel.innerHTML = followupHTML;
}

// ========== CHAT DISPLAY ==========

function addMessage(sender, text) {
    const chatBox = document.getElementById('chatBox');

    // Clear welcome message on first message
    const welcome = chatBox.querySelector('.welcome-message');
    if (welcome) welcome.remove();

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.innerHTML = highlightMedicalTerms(text);

    messageDiv.appendChild(contentDiv);
    chatBox.appendChild(messageDiv);

    // Auto scroll to bottom
    chatBox.parentElement.scrollTop = chatBox.parentElement.scrollHeight;

    // Save to history
    chatHistory.push({ sender, text, timestamp: new Date().toLocaleTimeString() });
    saveChatHistory();
}

function highlightMedicalTerms(text) {
    let highlighted = text;
    MEDICAL_TERMS.forEach(term => {
        const regex = new RegExp(`\\b${term}\\b`, 'gi');
        highlighted = highlighted.replace(regex, `<span class="highlight-term">${term}</span>`);
    });
    return highlighted;
}

function setInput(text) {
    document.getElementById('symptomInput').value = text;
    document.getElementById('symptomInput').focus();
}

function copyResult(text) {
    navigator.clipboard.writeText(text).then(() => {
        alert('Copied to clipboard!');
    });
}

// ========== CHAT HISTORY ==========

function saveChatHistory() {
    localStorage.setItem('chatHistory', JSON.stringify(chatHistory.slice(-10)));
}

function loadChatHistory() {
    const saved = localStorage.getItem('chatHistory');
    if (saved) {
        chatHistory = JSON.parse(saved);
        const chatBox = document.getElementById('chatBox');
        chatHistory.forEach(msg => {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${msg.sender}`;
            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';
            contentDiv.innerHTML = highlightMedicalTerms(msg.text);
            messageDiv.appendChild(contentDiv);
            chatBox.appendChild(messageDiv);
        });
    }
}

function clearHistory() {
    if (confirm('Clear all chat history?')) {
        chatHistory = [];
        localStorage.removeItem('chatHistory');
        document.getElementById('chatBox').innerHTML = `
            <div class="welcome-message">
                <div class="welcome-icon">🏥</div>
                <h2>Welcome to MediChat</h2>
                <p>Ask me about symptoms, diseases, health tips, and more!</p>
                <div class="quick-options">
                    <button class="quick-btn" onclick="setInput('I have fever')">Fever</button>
                    <button class="quick-btn" onclick="setInput('How to manage stress')">Stress</button>
                    <button class="quick-btn" onclick="setInput('Sleep tips')">Sleep</button>
                    <button class="quick-btn" onclick="setInput('Diet advice')">Diet</button>
                </div>
            </div>
        `;
    }
}

// ========== TAB MANAGEMENT ==========

function setActiveTab(tab) {
    const tabs = document.querySelectorAll('.tab-btn');
    tabs.forEach(t => t.classList.remove('active'));
    event.target.classList.add('active');

    if (tab === 'diagnosis' && currentDiagnosis) {
        handleDiagnosis(currentDiagnosis);
    } else if (tab === 'history') {
        showChatHistory();
    }
}

function showChatHistory() {
    const historyHTML = `
        <div class="diagnosis-result">
            <div class="result-title">📜 Chat History</div>
            ${chatHistory.slice(-5).reverse().map(msg => `
                <div class="result-item">
                    <div class="result-label">${msg.sender.toUpperCase()} - ${msg.timestamp}</div>
                    <div class="result-value">${msg.text.substring(0, 100)}...</div>
                </div>
            `).join('')}
            <div class="action-buttons">
                <button class="action-btn" onclick="clearHistory()">🗑️ Clear All</button>
            </div>
        </div>
    `;
    document.getElementById('resultsPanel').innerHTML = historyHTML;
}

// ========== EXPORT FOR GLOBAL SCOPE ==========

window.setInput = setInput;
window.copyResult = copyResult;
window.clearHistory = clearHistory;
window.askFollowup = askFollowup;
window.speakBot = speakBot;
