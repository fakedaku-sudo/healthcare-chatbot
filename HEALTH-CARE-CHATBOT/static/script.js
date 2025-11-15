/* ========================================
   MEDICHAT - MODERN SCRIPT WITH Q&A
   ======================================== */

// ========== GLOBAL VARIABLES ==========

let recognition;
let isListening = false;
let voiceEnabled = localStorage.getItem('voiceEnabled') === 'true';
let chatHistory = [];
let currentDiagnosis = null;
let desiredListening = false; // when true, keep restarting recognition for continuous listening

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
            // Use the first alternative transcript if available
            const transcript = (event.results[i] && event.results[i][0] && event.results[i][0].transcript) || (event.results[i] && event.results[i].transcript) || '';
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
            // Place the recognized text into the input and auto-send as a command
            const inputEl = document.getElementById('symptomInput');
            if (inputEl) {
                inputEl.value = finalTranscript;
                // small delay to allow UI update before sending
                setTimeout(() => {
                    try {
                        sendMessage();
                    } catch (e) {
                        console.warn('Auto-send failed:', e);
                    }
                }, 350);
            }
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
        // If the user enabled continuous listening, restart recognition
        if (desiredListening) {
            setTimeout(() => {
                try {
                    recognition.start();
                } catch (e) {
                    console.warn('Restart recognition failed:', e);
                }
            }, 250);
        }
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
        // user requested to stop listening
        desiredListening = false;
        recognition.stop();
    } else {
        // start continuous listening until user stops
        desiredListening = true;
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
        if (data.error) {
            addMessage('bot', data.error);
            speakBot(data.error);
            return;
        }

        currentDiagnosis = input;

        if (data.disease && data.disease !== 'Unknown') {
            const symptomsText = (data.symptoms_present || []).map(s => s.replace(/_/g, ' ')).join(', ') || input;
            addMessage('bot', data.result_message);
            speakBot(data.result_message);

            // Build precautions list
            const precautions = data.precautions || [];
            const precautionsHTML = precautions.length > 0 
                ? precautions.map(p => `<li>${p}</li>`).join('')
                : '<li>Consult a healthcare professional</li>';

            // Build other diseases list
            const otherDiseasesHTML = data.all_possible_diseases && data.all_possible_diseases.length > 1
                ? `<div class="result-item">
                   <div class="result-label">Other Possible Diseases</div>
                   <div class="result-value">${data.all_possible_diseases.filter(d => d !== data.disease).join(', ')}</div>
                   </div>`
                : '';

            const resultHTML = `
                <div class="diagnosis-result">
                    <div class="result-title">🏥 Comprehensive Diagnosis</div>
                    
                    <div class="result-item">
                        <div class="result-label">Detected Symptoms</div>
                        <div class="result-value">${symptomsText}</div>
                    </div>

                    <div class="result-item">
                        <div class="result-label">Primary Disease</div>
                        <div class="result-value" style="color: #42A5F5; font-weight: bold; font-size: 15px;">${data.disease}</div>
                    </div>

                    <div class="result-item">
                        <div class="result-label">Description</div>
                        <div class="result-value">${data.description || 'No description available'}</div>
                    </div>

                    ${otherDiseasesHTML}

                    <div class="result-item">
                        <div class="result-label">Confidence Level</div>
                        <div class="confidence-bar">
                            <div class="confidence-fill" style="width: ${Math.min(data.confidence * 100, 100)}%"></div>
                        </div>
                        <div class="result-value">${Math.round(Math.min(data.confidence * 100, 100))}%</div>
                    </div>

                    <div class="result-item">
                        <div class="result-label">Precautions</div>
                        <ul class="precaution-list">
                            ${precautionsHTML}
                        </ul>
                    </div>

                    <div class="action-buttons">
                        <button class="action-btn" onclick="copyResult('${data.disease}')">📋 Copy</button>
                        <button class="action-btn" onclick="speakBot('${data.result_message.replace(/'/g, "\\'")}')">🔊 Read</button>
                    </div>
                </div>
            `;
            resultsPanel.innerHTML = resultHTML;
        } else {
            const msg = 'Please describe your symptoms more clearly. Example: "I have fever, cough and headache"';
            addMessage('bot', msg);
            speakBot(msg);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        const errorMsg = 'An error occurred during diagnosis. Please try again.';
        addMessage('bot', errorMsg);
        speakBot(errorMsg);
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
    
    // Find and mark the correct button as active
    if (tab === 'diagnosis') {
        document.getElementById('diagnosisTab').classList.add('active');
        if (currentDiagnosis) {
            handleDiagnosis(currentDiagnosis);
        }
    } else if (tab === 'health-tips') {
        document.getElementById('healthTipsTab').classList.add('active');
        showHealthTips();
    } else if (tab === 'history') {
        document.getElementById('historyBtn').classList.add('active');
        showChatHistory();
    }
}

function showChatHistory() {
    const historyHTML = `
        <div class="diagnosis-result">
            <div class="result-title">📜 Chat History</div>
            ${chatHistory.length > 0 
                ? chatHistory.slice(-10).reverse().map((msg, idx) => `
                    <div class="result-item">
                        <div class="result-label">${msg.sender.toUpperCase()} - ${msg.timestamp}</div>
                        <div class="result-value">${msg.text.substring(0, 150)}</div>
                    </div>
                `).join('')
                : '<div class="result-item"><div class="result-value">No chat history yet</div></div>'
            }
            ${chatHistory.length > 0 ? `<div class="action-buttons">
                <button class="action-btn" onclick="clearHistory()">🗑️ Clear All</button>
            </div>` : ''}
        </div>
    `;
    document.getElementById('resultsPanel').innerHTML = historyHTML;
}

function showHealthTips() {
    const tipsHTML = `
        <div class="diagnosis-result">
            <div class="result-title">💡 Health Tips</div>
            
            <div class="result-item">
                <div class="result-label">🏃 Exercise</div>
                <div class="result-value">Get at least 30 minutes of moderate exercise daily</div>
            </div>

            <div class="result-item">
                <div class="result-label">🛏️ Sleep</div>
                <div class="result-value">Aim for 7-9 hours of quality sleep each night</div>
            </div>

            <div class="result-item">
                <div class="result-label">🥗 Nutrition</div>
                <div class="result-value">Eat a balanced diet with fruits, vegetables, and whole grains</div>
            </div>

            <div class="result-item">
                <div class="result-label">💧 Hydration</div>
                <div class="result-value">Drink at least 8 glasses of water daily</div>
            </div>

            <div class="result-item">
                <div class="result-label">🧘 Stress Management</div>
                <div class="result-value">Practice meditation, yoga, or deep breathing exercises</div>
            </div>

            <div class="result-item">
                <div class="result-label">🏥 Regular Check-ups</div>
                <div class="result-value">Visit your doctor for regular health screenings</div>
            </div>
        </div>
    `;
    document.getElementById('resultsPanel').innerHTML = tipsHTML;
}

// ========== EXPORT FOR GLOBAL SCOPE ==========

window.setInput = setInput;
window.copyResult = copyResult;
window.clearHistory = clearHistory;
window.askFollowup = askFollowup;
window.speakBot = speakBot;

// ========== THEME TOGGLE ==========

let isDarkTheme = localStorage.getItem('theme') === 'dark' || true;

function toggleTheme() {
    isDarkTheme = !isDarkTheme;
    localStorage.setItem('theme', isDarkTheme ? 'dark' : 'light');
    updateTheme();
}

function updateTheme() {
    const themeBtn = document.getElementById('themeToggle');
    const root = document.documentElement;
    
    if (isDarkTheme) {
        themeBtn.textContent = '🌙';
        root.style.setProperty('--bg-dark', '#0D2A45');
        root.style.setProperty('--bg-darker', '#081820');
        root.style.setProperty('--text-primary', '#ffffff');
    } else {
        themeBtn.textContent = '☀️';
        root.style.setProperty('--bg-dark', '#F5F5F5');
        root.style.setProperty('--bg-darker', '#FFFFFF');
        root.style.setProperty('--text-primary', '#1a1a1a');
    }
}

// Initialize theme on page load
window.addEventListener('load', function() {
    updateTheme();
    const themeBtn = document.getElementById('themeToggle');
    if (themeBtn) {
        themeBtn.addEventListener('click', toggleTheme);
    }
});
