document.addEventListener('DOMContentLoaded', function() {
    const symptomInput = document.getElementById('symptomInput');
    const knownDiseaseInput = document.getElementById('knownDiseaseInput');
    const daysInput = document.getElementById('daysInput');
    const ageInput = document.getElementById('ageInput');
    const submitBtn = document.getElementById('submitBtn');
    const resetBtn = document.getElementById('resetBtn');
    const followupContainer = document.getElementById('followupContainer');
    const followupQuestions = document.getElementById('followupQuestions');
    const followupSubmit = document.getElementById('followupSubmit');
    const suggestionsList = document.getElementById('suggestions');
    const chatBox = document.getElementById('chatBox');
    const resultsContainer = document.getElementById('resultsContainer');
    const inputSection = document.querySelector('.input-section');

    // Handle symptom input with suggestions
    symptomInput.addEventListener('input', async function(e) {
        const value = e.target.value.trim();
        
        if (value.length < 2) {
            suggestionsList.classList.remove('active');
            return;
        }

        try {
            const response = await fetch('/api/suggest_symptoms', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ text: value })
            });

            const data = await response.json();
            displaySuggestions(data.suggestions);
        } catch (error) {
            console.error('Error fetching suggestions:', error);
        }
    });

    // Display suggestions
    function displaySuggestions(suggestions) {
        suggestionsList.innerHTML = '';
        
        if (suggestions.length === 0) {
            suggestionsList.classList.remove('active');
            return;
        }

        suggestions.forEach(suggestion => {
            const li = document.createElement('li');
            li.textContent = suggestion.replace(/_/g, ' ');
            li.addEventListener('click', function() {
                symptomInput.value = suggestion.replace(/_/g, ' ');
                suggestionsList.classList.remove('active');
            });
            suggestionsList.appendChild(li);
        });

        suggestionsList.classList.add('active');
    }

    // Close suggestions when clicking outside
    document.addEventListener('click', function(e) {
        if (e.target !== symptomInput) {
            suggestionsList.classList.remove('active');
        }
    });

    // Submit diagnosis
    submitBtn.addEventListener('click', async function() {
        const symptom = symptomInput.value.trim();
        const days = parseInt(daysInput.value);

        // Accept either symptom or known disease
        const knownDisease = knownDiseaseInput.value.trim();
        if (!symptom && !knownDisease) {
            showError('Please enter a symptom');
            return;
        }

        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="loading"></span> Diagnosing...';

        try {
            const response = await fetch('/api/diagnose', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                        symptom: symptom,
                        days: days,
                        age: parseInt(ageInput.value) || null,
                        known_disease: knownDisease
                    })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Invalid symptom');
            }

            const data = await response.json();
                    // If API returns follow-up questions, show them
                    if (data.followup && data.followup.length > 0) {
                        showFollowupQuestions(data.followup, data.disease);
            } else {
                displayResults(data, symptom || knownDisease, days);
                // Add messages to chat
                addMessage('user', `I have ${symptom || knownDisease} for ${days} day(s), age ${ageInput.value}`);
                addMessage('bot', `I've analyzed your symptoms. You may have ${data.disease}.`);
            }

        } catch (error) {
            showError(error.message || 'Error getting diagnosis');
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Get Diagnosis';
        }
    });

    // Display results
    function displayResults(data, symptom, days) {
        document.getElementById('diseaseResult').textContent = data.disease;
        document.getElementById('descriptionResult').textContent = data.description;
        document.getElementById('conditionResult').textContent = data.condition;

        const precautionsList = document.getElementById('precautionsList');
        precautionsList.innerHTML = '';
        
        if (data.precautions && data.precautions.length > 0) {
            data.precautions.forEach(precaution => {
                const li = document.createElement('li');
                li.textContent = precaution;
                precautionsList.appendChild(li);
            });
        } else {
            precautionsList.innerHTML = '<li>No specific precautions available</li>';
        }

        inputSection.style.display = 'none';
        resultsContainer.style.display = 'block';
    }

    let currentFollowupDisease = null;
    function showFollowupQuestions(questions, disease) {
        currentFollowupDisease = disease || null;
        followupContainer.style.display = 'block';
        followupQuestions.innerHTML = '';
        questions.forEach(q => {
            const div = document.createElement('div');
            div.className = 'form-group';
            const label = document.createElement('label');
            label.textContent = q;
            const input = document.createElement('input');
            input.type = 'text';
            input.dataset.question = q;
            input.className = 'followup-input';
            div.appendChild(label);
            div.appendChild(input);
            followupQuestions.appendChild(div);
        });
    }

        followupSubmit.addEventListener('click', async function() {
        const inputs = document.querySelectorAll('.followup-input');
        const answers = {};
        inputs.forEach(i => { answers[i.dataset.question] = i.value.trim(); });

        // Send follow-up answers to backend
        followupSubmit.disabled = true;
        followupSubmit.textContent = 'Submitting...';
        try {
            const response = await fetch('/api/diagnose_followup', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ answers, disease: currentFollowupDisease, age: parseInt(ageInput.value) || null })
            });
            const data = await response.json();
            displayResults(data, symptomInput.value || knownDiseaseInput.value, parseInt(daysInput.value));
            addMessage('bot', data.result_message || `Final result: ${data.disease}`);
            followupContainer.style.display = 'none';
        } catch (err) {
            showError('Error submitting follow-up answers');
        } finally {
            followupSubmit.disabled = false;
            followupSubmit.textContent = 'Submit Answers';
        }
    });

    // Reset form
    resetBtn.addEventListener('click', function() {
        symptomInput.value = '';
        daysInput.value = '1';
        inputSection.style.display = 'block';
        resultsContainer.style.display = 'none';
        symptomInput.focus();
    });

    // Show error message
    function showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = message;
        inputSection.insertBefore(errorDiv, inputSection.firstChild);
        
        setTimeout(() => {
            errorDiv.remove();
        }, 5000);
    }

    // Add message to chat box
    function addMessage(sender, text) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        const p = document.createElement('p');
        p.textContent = text;
        messageDiv.appendChild(p);
        chatBox.appendChild(messageDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    // Focus on symptom input
    symptomInput.focus();
});
