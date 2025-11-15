# Voice Assistant & Disease Search - Testing Guide

## 🎤 How to Test Voice Features

### Test 1: Microphone Input
1. Click the 🎤 microphone button in the "Describe your symptoms" field
2. Speak clearly: "I have a fever and cough"
3. Your speech should appear in the input field
4. Select duration and age, then click "Get Diagnosis"

### Test 2: Auto-Read Results (Voice Toggle)
1. Click the 🔊 voice button in the header (top-right area)
   - Button should turn pink/glow when enabled
2. Enter a symptom (e.g., "fever") and submit
3. When results appear, they should be **automatically read aloud** (if enabled)
4. Toggle voice off and submit again - results won't be auto-read

### Test 3: Play Button (Manual Voice Replay)
1. Get a diagnosis (either search by symptom or disease name)
2. In the results card at bottom, look for the 🔊 **play button**
3. Click it to hear the full diagnosis read aloud
4. **This works REGARDLESS of the voice toggle being on/off**

---

## 🔍 How to Test Disease Search & Precautions

### Test 1: Search by Symptom
**Input:** Symptom name  
**Example:** "fever", "cough", "headache", "nausea"

**Steps:**
1. Type symptom in "Describe your symptoms" field
2. Set duration: 3 days
3. Set age: 30
4. Click "Get Diagnosis"

**Expected Results:**
- Disease diagnosis appears
- Description shows (e.g., "Dengue is a mosquito-borne...")
- **Precautions show** as a bulleted list:
  - drink plenty of fluids
  - avoid mosquito bites
  - take paracetamol
  - consult doctor
- Play button reads all precautions aloud

### Test 2: Search by Disease Name
**Input:** Disease name  
**Example:** "dengue", "malaria", "diabetes", "asthma"

**Steps:**
1. Leave symptoms field empty
2. Type disease name in "Or search by disease" field
3. Set age (if needed): 30
4. Click "Get Diagnosis"

**Expected Results:**
- Follow-up questions may appear
- Final diagnosis shows with precautions
- Precautions are disease-specific

### Test 3: Precautions with Voice
1. Get diagnosis (symptom or disease)
2. Precautions appear in results
3. Click play button 🔊
4. **Voice reads:** "Recommended precautions: drink plenty of fluids. avoid mosquito bites. take paracetamol. consult doctor."

---

## 📋 Example Test Cases

### Example 1: Fever Search
**Input:**
- Symptom: "fever"
- Days: 3
- Age: 30

**Expected Output:**
```
Disease: Dengue
Description: Dengue is a mosquito-borne viral infection...
Condition: Follow suggested precautions and consult a doctor if symptoms worsen.
Precautions:
  ✓ drink plenty of fluids
  ✓ avoid mosquito bites
  ✓ take paracetamol
  ✓ consult doctor
```

### Example 2: Diabetes Search
**Input:**
- Disease: "diabetes"
- Age: 45

**Expected Output:**
```
Disease: Diabetes
Description: Diabetes is a chronic condition affecting blood sugar...
Condition: You should take the consultation from doctor.
Precautions:
  ✓ eat healthy diet
  ✓ exercise regularly
  ✓ monitor blood sugar
  ✓ take insulin if needed
```

### Example 3: Multiple Symptoms
**Input:**
- Symptom: "fever"
- Additional symptoms (follow-ups): "chills", "body ache"
- Days: 5
- Age: 25

**Expected Output:**
```
Disease: Malaria or Dengue
Precautions will be shown based on final diagnosis
Voice will read: "Diagnosis: You may have Malaria or Dengue. Description: ... Precautions: ..."
```

---

## 🐛 Troubleshooting

### Microphone Not Working
**Solution:**
- Check browser permissions (Chrome Settings → Privacy & Security → Microphone)
- Allow `localhost:5000` to use microphone
- Try refreshing the page
- Test in Chrome/Edge first (best support)

### Voice Not Speaking
**Solution:**
- Click voice toggle 🔊 to enable
- Use play button to manually trigger
- Check system volume is not muted
- Check browser doesn't have audio disabled
- Try a different browser (Firefox, Chrome)

### Precautions Not Showing
**Solution:**
- Make sure you enter a valid symptom or disease
- Check CSV files exist:
  - `symptom_precaution.csv`
  - `symptom_Description.csv`
- Server should have reloaded data on startup
- Check console for error messages (F12)

### Server Error (400/500)
**Solution:**
- Refresh page (F5)
- Check symptom/disease spelling
- Try a common symptom first: "fever", "cough", "headache"
- Restart Flask server:
  - Press Ctrl+C in terminal
  - Run: `python app.py`

---

## 📱 Browser Compatibility

| Browser | Voice Input | Voice Output | Precautions |
|---------|-----------|------------|------------|
| Chrome  | ✅ Full   | ✅ Full    | ✅ Yes     |
| Edge    | ✅ Full   | ✅ Full    | ✅ Yes     |
| Firefox | ✅ Full   | ✅ Full    | ✅ Yes     |
| Safari  | ⚠️ Limited | ✅ Full   | ✅ Yes     |
| Mobile  | ✅ Yes    | ✅ Yes     | ✅ Yes     |

---

## 🎯 Key Features Verified

✅ **Microphone Button**
- Located inside "Describe your symptoms" input field
- Click to start listening
- Speech auto-fills input field

✅ **Voice Toggle Button**  
- Located in header (top-right)
- Pink glow when enabled
- Auto-reads results when enabled

✅ **Play Button**
- Located in results card after diagnosis
- Reads full diagnosis with precautions
- Works regardless of toggle state

✅ **Disease Search**
- Search by symptom name
- Search by disease name
- Returns precautions for all diseases

✅ **Precautions Display**
- Shows as bulleted list in results
- 4 precautions per disease
- Read aloud by voice

---

## 📊 Data Sources

**Precaution Data:** `symptom_precaution.csv`
- Contains 80+ diseases
- 4 precautions per disease
- Case-insensitive matching enabled

**Description Data:** `symptom_Description.csv`
- Detailed descriptions for each disease
- Used in voice narration

**Symptom Data:** `Training.csv` & `Testing.csv`
- 132 symptoms
- 41 diseases
- ML classification model

---

## 🔧 Technical Details

### Voice Recognition API
- **Technology:** Web Speech API (SpeechRecognition)
- **Supported Languages:** English (en-US)
- **Auto-start:** Press microphone button
- **Timeout:** Stops automatically after silence

### Text-to-Speech API
- **Technology:** Web Speech API (SpeechSynthesis)
- **Rate:** 0.9x (slightly slower for clarity)
- **Volume:** 100%
- **Language:** Browser default

### Disease Matching
- **Method:** Case-insensitive substring matching
- **Fallback:** Exact disease name lookup
- **Precautions:** Direct CSV lookup with error handling

---

## 💡 Tips for Best Results

1. **Clear speech for microphone:**
   - Speak slowly and clearly
   - Minimize background noise
   - Use built-in microphone (if available)

2. **Use common symptoms:**
   - "fever", "cough", "headache", "nausea"
   - "chills", "body ache", "fatigue"
   - Avoid very specific symptoms first

3. **For accurate diagnosis:**
   - Provide age and duration
   - Follow up with additional questions
   - Answer honestly

4. **Accessibility features:**
   - Voice feature helps blind users
   - Play button can be used anytime
   - Chat history is searchable

---

**Last Updated:** November 15, 2025  
**Status:** Ready for Testing ✅
