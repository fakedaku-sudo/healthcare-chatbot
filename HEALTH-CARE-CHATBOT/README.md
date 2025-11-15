# Healthcare ChatBot

A symptom-based disease diagnosis chatbot using machine learning. Features both a web interface and command-line interface.

## Features
- 🏥 Symptom-based disease diagnosis
- 🤖 Machine learning powered (Decision Tree & SVM classifiers)
- 🌐 Interactive web interface with real-time suggestions
- 📊 Severity assessment based on symptom duration
- 💊 Medical precautions and recommendations
- 🔍 Pattern matching for symptom suggestions

## Installation

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Ensure required CSV files are in the project root:**
- `Training.csv` - Training dataset with symptoms and diseases
- `Testing.csv` - Testing dataset
- `symptom_Description.csv` - Disease descriptions
- `Symptom_severity.csv` - Symptom severity levels
- `symptom_precaution.csv` - Precautions for each disease

## Running the Application

### Web Interface (Recommended) ⭐
```bash
python app.py
```
Then open your browser and navigate to: **http://localhost:5000**

### Command-Line Interface
```bash
python chat_bot.py
```

## Project Structure
```
├── app.py                          # Flask web application
├── chat_bot.py                     # Original CLI chatbot
├── requirements.txt                # Python dependencies
├── Training.csv                    # Training dataset
├── Testing.csv                     # Testing dataset
├── symptom_Description.csv         # Disease descriptions
├── Symptom_severity.csv            # Symptom severity data
├── symptom_precaution.csv          # Precautions database
├── templates/
│   └── index.html                  # Web UI HTML template
└── static/
    ├── style.css                   # UI styling
    └── script.js                   # Frontend interactions
```

## How It Works
1. User enters a symptom
2. System suggests matching symptoms
3. User confirms the symptom and duration
4. ML model analyzes and predicts possible diseases
5. System provides disease details and precautions

## Technologies Used
- **Backend:** Flask (Python web framework)
- **Machine Learning:** scikit-learn (Decision Tree, SVM)
- **Data:** Pandas, NumPy
- **Frontend:** HTML5, CSS3, JavaScript
- **Speech:** pyttsx3 (text-to-speech)

## Important Notes
⚠️ **Disclaimer:** This chatbot is for educational purposes only and should NOT replace professional medical advice. Always consult with a qualified healthcare professional for accurate diagnosis.

## Troubleshooting

**Port already in use?** Edit `app.py` and change port to 5001 or another available port.

**Missing CSV files?** Ensure all required CSV files are in the project root directory.
