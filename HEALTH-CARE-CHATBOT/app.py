from flask import Flask, render_template, request, jsonify, send_file
import io
import datetime
import logging
import traceback
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
import os

# Base directory for data files (make file paths robust regardless of cwd)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# PDF generation (optional)
try:
    import importlib
    _rl_pages = importlib.import_module('reportlab.lib.pagesizes')
    _rl_pdfgen = importlib.import_module('reportlab.pdfgen.canvas')
    _rl_units = importlib.import_module('reportlab.lib.units')
    letter = getattr(_rl_pages, 'letter')
    canvas = _rl_pdfgen
    inch = getattr(_rl_units, 'inch')
    HAVE_REPORTLAB = True
except Exception:
    HAVE_REPORTLAB = False
    logging.warning('reportlab not installed; PDF reports will not be available. Install with `pip install reportlab`')

# Chatbot display name used in reports
CHATBOT_NAME = 'MediChat'
import re
import pandas as pd
import pyttsx3
from sklearn import preprocessing
from sklearn.tree import DecisionTreeClassifier, _tree
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.model_selection import cross_val_score
from sklearn.svm import SVC
import csv
# ==================== DATA LOADING ====================
logging.info('Loading data...')
training = pd.read_csv(os.path.join(BASE_DIR, 'Training.csv'))
testing = pd.read_csv(os.path.join(BASE_DIR, 'Testing.csv'))
cols = training.columns
cols = cols[:-1]
x = training[cols]
y = training['prognosis']
y1 = y

reduced_data = training.groupby(training['prognosis']).max()

# Mapping strings to numbers
le = preprocessing.LabelEncoder()
le.fit(y)
y = le.transform(y)

x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.33, random_state=42)
testx = testing[cols]
testy = testing['prognosis']
testy = le.transform(testy)

clf1 = DecisionTreeClassifier()
clf = clf1.fit(x_train, y_train)

# Print model scores
scores = cross_val_score(clf, x_test, y_test, cv=3)
logging.info('DecisionTree cross-val mean score: %.4f', scores.mean())

model = SVC()
model.fit(x_train, y_train)
logging.info('SVM test score: %.4f', model.score(x_test, y_test))

importances = clf.feature_importances_
indices = np.argsort(importances)[::-1]
features = cols

# ==================== GLOBAL DICTIONARIES ====================
severityDictionary = dict()
description_list = dict()
precautionDictionary = dict()

symptoms_dict = {}

for index, symptom in enumerate(x):
    symptoms_dict[symptom] = index
description_list = dict()
precautionDictionary = dict()

symptoms_dict = {}

for index, symptom in enumerate(x):
    symptoms_dict[symptom] = index

# ==================== HELPER FUNCTIONS ====================

# Create Flask app
app = Flask(__name__, static_folder='static', template_folder='templates')

def readn(nstr):
    """Text to speech function"""
    engine = pyttsx3.init()
    engine.setProperty('voice', "english+f5")
    engine.setProperty('rate', 130)
    engine.say(nstr)
    engine.runAndWait()
    engine.stop()

def getDescription():
    """Load disease descriptions from CSV"""
    global description_list
    with open(os.path.join(BASE_DIR, 'symptom_Description.csv')) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            _description = {row[0]: row[1]}
            description_list.update(_description)

def getSeverityDict():
    """Load symptom severity data from CSV"""
    global severityDictionary
    with open(os.path.join(BASE_DIR, 'Symptom_severity.csv')) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        try:
            for row in csv_reader:
                _diction = {row[0]: int(row[1])}
                severityDictionary.update(_diction)
        except:
            pass

def getprecautionDict():
    """Load precaution data from CSV"""
    global precautionDictionary
    with open(os.path.join(BASE_DIR, 'symptom_precaution.csv')) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_file:
            if row.strip() and not row.startswith('Disease'):
                parts = row.strip().split(',', 4)
                if len(parts) >= 5:
                    disease_name = parts[0].strip()
                    precautions = [parts[1].strip(), parts[2].strip(), parts[3].strip(), parts[4].strip()]
                    precautionDictionary[disease_name] = precautions

def calc_condition(exp, days):
    """Calculate severity condition"""
    sum_val = 0
    for item in exp:
        sum_val = sum_val + severityDictionary[item]
    
    if ((sum_val * days) / (len(exp) + 1) > 13):
        return "You should take the consultation from doctor."
    else:
        return "It might not be that bad but you should take precautions."

def extract_symptoms_from_text(text, symptom_list):
    """Extract symptoms from natural language text"""
    extracted_symptoms = []
    text_lower = text.lower()
    
    # Comprehensive symptom mapping with common phrases
    phrases = {
        'fever': ['fever', 'high temperature', 'temperature', 'hot', 'running fever'],
        'cough': ['cough', 'coughing', 'dry cough', 'wet cough', 'persistent cough'],
        'headache': ['headache', 'head pain', 'migraine', 'head ache'],
        'body ache': ['body ache', 'body pain', 'ache', 'pain in body', 'muscle ache', 'muscle pain'],
        'fatigue': ['fatigue', 'tired', 'tiredness', 'exhausted', 'weakness', 'weak'],
        'cold': ['cold', 'common cold', 'catch a cold'],
        'nausea': ['nausea', 'feel sick', 'vomiting', 'puke', 'feeling sick'],
        'diarrhea': ['diarrhea', 'loose motion', 'loose stools', 'loose motions'],
        'congestion': ['congestion', 'stuffy nose', 'runny nose', 'nasal congestion'],
        'sore throat': ['sore throat', 'throat pain', 'throat ache', 'painful throat'],
        'rash': ['rash', 'skin rash', 'spots', 'skin spots', 'hives'],
        'swelling': ['swelling', 'swollen', 'inflammation', 'inflamed'],
        'itching': ['itching', 'itchy', 'itches', 'scratching'],
        'chills': ['chills', 'shivering', 'shiver', 'cold chills'],
        'hair fall': ['hair fall', 'hair loss', 'hair falling', 'baldness', 'falling hair'],
        'knee knock': ['knee knock', 'knee knocking', 'knee issue', 'knee problem', 'knock knees'],
        'back pain': ['back pain', 'backache', 'lower back pain', 'upper back pain', 'back ache', 'backpain'],
        'chest pain': ['chest pain', 'chest ache', 'heart pain'],
        'shoulder pain': ['shoulder pain', 'shoulder ache', 'shoulder pain'],
        'hand pain': ['hand pain', 'hand ache', 'pain in hand', 'hand hurts'],
        'arm pain': ['arm pain', 'arm ache', 'pain in arm'],
        'leg pain': ['leg pain', 'leg ache', 'pain in leg'],
        'joint pain': ['joint pain', 'joint ache', 'joints hurt', 'arthritis'],
        'acne': ['acne', 'pimples', 'acne breakout', 'spots on face'],
        'skin rash': ['skin rash', 'rash', 'skin eruption'],
        'constipation': ['constipation', 'constipated', 'difficulty in bowel'],
        'indigestion': ['indigestion', 'acid reflux', 'bloating', 'gas'],
        'stomach pain': ['stomach pain', 'stomach ache', 'abdominal pain', 'belly pain'],
        'vomiting': ['vomiting', 'vomit', 'throwing up', 'retching'],
        'breathlessness': ['breathlessness', 'shortness of breath', 'difficulty breathing', 'breathless'],
        'cough variant': ['cough', 'dry cough', 'persistent cough'],
        'snoring': ['snoring', 'snore', 'snores'],
        'sleeplessness': ['sleeplessness', 'insomnia', 'can not sleep', 'unable to sleep'],
        'dizziness': ['dizziness', 'dizzy', 'vertigo', 'lightheaded'],
        'eye pain': ['eye pain', 'eye ache', 'pain in eyes'],
        'ear pain': ['ear pain', 'ear ache', 'earache'],
        'tooth pain': ['tooth pain', 'tooth ache', 'toothache'],
        'nosebleed': ['nosebleed', 'nose bleeding', 'bloody nose'],
        'bleeding': ['bleeding', 'bleed', 'bleeds'],
        'bruising': ['bruising', 'bruises', 'black and blue', 'contusion'],
        'numbness': ['numbness', 'numb', 'feel numb'],
        'tingling': ['tingling', 'pins and needles', 'prickling'],
        'tremor': ['tremor', 'trembling', 'shaking', 'tremors'],
        'weakness': ['weakness', 'weak', 'feeling weak'],
        'loss of appetite': ['loss of appetite', 'no appetite', 'not hungry'],
        'excessive hunger': ['excessive hunger', 'always hungry', 'hunger'],
        'excessive thirst': ['excessive thirst', 'very thirsty', 'constant thirst'],
        'frequent urination': ['frequent urination', 'urinating frequently', 'pee often'],
        'weight loss': ['weight loss', 'losing weight', 'lost weight'],
        'weight gain': ['weight gain', 'gaining weight', 'gained weight'],
        'mood swings': ['mood swings', 'mood changes', 'emotional changes', 'stress', 'feeling stress', 'stressed', 'stressed out'],
        'anxiety': ['anxiety', 'anxious', 'nervous', 'stress'],
        'depression': ['depression', 'depressed', 'sad', 'sadness'],
        'confusion': ['confusion', 'confused', 'disorientation'],
        'memory loss': ['memory loss', 'forgetfulness', 'forgetting', 'forgetful'],
        'high blood pressure': ['high blood pressure', 'high bp', 'hypertension'],
        'low blood pressure': ['low blood pressure', 'low bp', 'hypotension'],
        'heart palpitations': ['heart palpitations', 'palpitations', 'racing heart', 'heart racing'],
        'irregular heartbeat': ['irregular heartbeat', 'irregular pulse', 'arrhythmia'],
        'skin dryness': ['skin dryness', 'dry skin', 'skin is dry'],
        'skin oiliness': ['skin oiliness', 'oily skin', 'skin is oily'],
        'dandruff': ['dandruff', 'scalp flaking'],
    }
    
    # Extract symptoms from phrases
    for symptom_key, keywords in phrases.items():
        for keyword in keywords:
            if keyword in text_lower:
                # Find best matching symptom from training data
                for symptom in symptom_list:
                    symptom_normalized = symptom.replace('_', ' ').lower()
                    if (symptom_key.replace(' ', '_').lower() in symptom.lower() or 
                        symptom_normalized in symptom_key.lower() or
                        symptom_key.lower() in symptom_normalized):
                        if symptom not in extracted_symptoms:
                            extracted_symptoms.append(symptom)
                        break
    
    # If no symptoms extracted via phrases, try direct matching
    if not extracted_symptoms:
        for symptom in symptom_list:
            symptom_clean = symptom.replace('_', ' ').lower()
            if symptom_clean in text_lower or text_lower in symptom_clean:
                extracted_symptoms.append(symptom)
    
    return extracted_symptoms

def check_pattern(dis_list, inp):
    """Check pattern matching for symptoms"""
    pred_list = []
    inp = inp.replace(' ', '_')
    patt = f"{inp}"
    regexp = re.compile(patt)
    pred_list = [item for item in dis_list if regexp.search(item)]
    if (len(pred_list) > 0):
        return 1, pred_list
    else:
        return 0, []

def sec_predict(symptoms_exp):
    """Secondary prediction using Decision Tree"""
    df = pd.read_csv(os.path.join(BASE_DIR, 'Training.csv'))
    X = df.iloc[:, :-1]
    y = df['prognosis']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=20)
    rf_clf = DecisionTreeClassifier()
    rf_clf.fit(X_train, y_train)

    symptoms_dict_local = {symptom: index for index, symptom in enumerate(X)}
    input_vector = np.zeros(len(symptoms_dict_local))
    for item in symptoms_exp:
        input_vector[[symptoms_dict_local[item]]] = 1

    return rf_clf.predict([input_vector])

def print_disease(node):
    """Extract disease from tree node"""
    node = node[0]
    val = node.nonzero()
    disease = le.inverse_transform(val[0])
    return list(map(lambda x: x.strip(), list(disease)))

def get_precautions_for_disease(disease_name):
    """Get precautions for a disease, with case-insensitive matching"""
    # Try exact match first
    if disease_name in precautionDictionary:
        return precautionDictionary[disease_name]
    
    # Try case-insensitive match
    disease_lower = disease_name.lower().strip()
    for prec_disease, precautions in precautionDictionary.items():
        if prec_disease.lower().strip() == disease_lower:
            return precautions
    
    # If no match found, return empty list
    return []


def derive_common_treatments(disease_name):
    """Attempt to derive common treatments from the precautionDictionary or description_list."""
    if not disease_name:
        return []

    # Try precautionDictionary first
    treatments = []
    try:
        precs = precautionDictionary.get(disease_name, [])
        if not precs:
            # Try case-insensitive match
            for k, v in precautionDictionary.items():
                if k.lower().strip() == disease_name.lower().strip():
                    precs = v
                    break
        # Keywords that indicate a treatment or medicine
        treatment_keywords = ['take', 'treatment', 'antibiotic', 'antiviral', 'insulin', 'inhaler', 'physiotherapy', 'antimalarial', 'antacids', 'antihistamine', 'analgesic', 'pain reliever', 'ppis', 'ppi']
        for p in precs:
            lp = p.lower()
            if any(kw in lp for kw in treatment_keywords):
                treatments.append(p)
    except Exception:
        pass

    # If none found, try description_list and pick sentences that look like treatments
    if not treatments:
        desc = description_list.get(disease_name, '')
        if not desc:
            # case-insensitive fallback
            for k, v in description_list.items():
                if k.lower().strip() == disease_name.lower().strip():
                    desc = v
                    break
        if desc:
            # split by comma and pick items containing treatment-like keywords
            parts = [p.strip() for p in re.split(r'[,;]\s*', desc) if p.strip()]
            for p in parts:
                lp = p.lower()
                if any(kw in lp for kw in ['take', 'treatment', 'use', 'apply', 'rest', 'therapy', 'inhaler', 'antibiotic', 'antimalarial', 'antacid']):
                    treatments.append(p)

    # Deduplicate and return
    seen = set()
    out = []
    for t in treatments:
        if t not in seen:
            out.append(t)
            seen.add(t)
    # Normalize into informative sentences
    informative = []
    for t in out:
        s = t.strip()
        # capitalize first letter
        if s and not s[0].isupper():
            s = s[0].upper() + s[1:]
        if not s.endswith('.'):
            s = s + '.'
        informative.append(s)

    # If nothing found, provide general guidance
    if not informative:
        informative = [
            'Rest and stay well hydrated.',
            'Symptomatic treatment as needed (e.g. paracetamol for fever or pain) under medical advice.',
            'Seek medical consultation for specific prescription medicines and further evaluation.'
        ]

    # Add a short general safety note
    if 'Seek medical' not in ' '.join(informative):
        informative.append('Seek medical attention if symptoms worsen, such as difficulty breathing, severe pain, or high fever.')

    return informative

# ==================== INITIALIZE DATA ====================
getSeverityDict()
getDescription()
getprecautionDict()

chk_dis = ",".join(cols).split(",")

# ==================== FLASK ROUTES ====================

@app.route('/')
def index():
    """Serve the main web interface"""
    return render_template('index.html', symptoms=list(cols))

@app.route('/api/suggest_symptoms', methods=['POST'])
def suggest_symptoms():
    """API endpoint for symptom suggestions"""
    try:
        data = request.json or {}
        input_text = data.get('text', '').strip()
        conf, cnf_dis = check_pattern(chk_dis, input_text)
        return jsonify({'suggestions': cnf_dis})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/diagnose', methods=['POST'])
def diagnose():
    """API endpoint for diagnosis using the decision tree algorithm from chat_bot.py"""
    try:
        data = request.json or {}
        disease_input = data.get('symptoms', '').strip()  # Changed to 'symptoms'
        num_days = int(data.get('days', 1))
        age = data.get('age', None)
        known = data.get('known_disease', '').strip()

        # Accept either symptom or known disease
        if known:
            disease_input = known

        if not disease_input:
            return jsonify({'error': 'Please enter symptoms or disease'}), 400

        # Extract ALL symptoms from natural language text
        extracted_symptoms = extract_symptoms_from_text(disease_input, chk_dis)
        
        if not extracted_symptoms:
            # If no symptoms extracted, try to match as disease name
            try:
                matches = [d for d in le.classes_ if disease_input.lower() in d.lower()]
                if matches:
                    result_disease = matches[0]
                    precautions = get_precautions_for_disease(result_disease)
                    description = description_list.get(result_disease, "No description available")
                    derived = derive_common_treatments(result_disease)
                    return jsonify({
                        'disease': result_disease,
                        'description': description,
                        'precautions': precautions,
                        'derived_treatments': derived,
                        'result_message': f"You asked about {result_disease}",
                        'symptoms_present': [],
                        'confidence': 1.0
                    })
                else:
                    return jsonify({'error': 'Please describe your symptoms clearly. Example: "I have fever and cough"'}), 400
            except Exception:
                return jsonify({'error': 'Please describe your symptoms clearly'}), 400

        # ==================== TREE TRAVERSAL FOR MULTIPLE SYMPTOMS ====================
        tree_ = clf.tree_
        feature_name = [
            cols[i] if i != _tree.TREE_UNDEFINED else "undefined!"
            for i in tree_.feature
        ]

        # Track predictions from multiple symptoms
        all_predictions = []
        all_symptoms_present = set()

        # Process each extracted symptom
        for symptom_input in extracted_symptoms:
            symptoms_present = []
            present_disease = None
            symptoms_given = []

            # Normalize symptom for matching against tree feature names
            norm_symptom = str(symptom_input).replace('_', ' ').strip().lower()

            def recurse(node, depth):
                nonlocal present_disease, symptoms_given, symptoms_present

                if tree_.feature[node] != _tree.TREE_UNDEFINED:
                    name = feature_name[node]
                    threshold = tree_.threshold[node]

                    # Normalize feature name for case/underscore-insensitive comparison
                    name_norm = str(name).replace('_', ' ').strip().lower()

                    # Treat match if normalized names are equal
                    if name_norm == norm_symptom:
                        val = 1
                    else:
                        val = 0

                    if val <= threshold:
                        recurse(tree_.children_left[node], depth + 1)
                    else:
                        symptoms_present.append(name)
                        recurse(tree_.children_right[node], depth + 1)
                else:
                    present_disease = print_disease(tree_.value[node])
                    try:
                        # Ensure we use a single disease label for lookup
                        pd_key = present_disease[0] if isinstance(present_disease, (list, tuple, np.ndarray)) else present_disease
                        red_cols = reduced_data.columns
                        row = reduced_data.loc[pd_key]
                        # row.values may be 1D or 2D depending on lookup, handle both
                        vals = row.values
                        if vals.ndim > 1:
                            vals = vals[0]
                        symptoms_given = list(red_cols[np.array(vals).nonzero()[0]])
                    except Exception:
                        symptoms_given = []

            # Start tree traversal for this symptom
            recurse(0, 1)
            
            if present_disease:
                all_symptoms_present.update(symptoms_present)
                all_predictions.append({
                    'disease': present_disease[0],
                    'symptoms': symptoms_present,
                    'confidence': len(symptoms_present) / max(len(symptoms_given), 1) if symptoms_given else 0
                })

        if not all_predictions:
            return jsonify({'error': 'Could not diagnose with given symptoms'}), 400

        # Find most common disease prediction
        disease_scores = {}
        for pred in all_predictions:
            disease = pred['disease']
            score = pred['confidence']
            disease_scores[disease] = disease_scores.get(disease, 0) + score

        # Get top disease
        top_disease = max(disease_scores, key=disease_scores.get)
        avg_confidence = disease_scores[top_disease] / len(all_predictions)

        description = description_list.get(top_disease, "No description available")
        precautions = get_precautions_for_disease(top_disease)
        derived = derive_common_treatments(top_disease)
        
        # Create comprehensive message
        symptoms_str = ', '.join([s.replace('_', ' ').title() for s in extracted_symptoms])
        result_msg = f"Based on your symptoms ({symptoms_str}), you may have {top_disease}"
        
        if len(all_predictions) > 1:
            other_diseases = [p['disease'] for p in all_predictions if p['disease'] != top_disease]
            if other_diseases:
                result_msg += f" or possibly {', '.join(set(other_diseases))}"

        return jsonify({
            'disease': top_disease,
            'description': description,
            'condition': 'Multiple symptoms detected',
            'precautions': precautions,
            'derived_treatments': derived,
            'result_message': result_msg,
            'symptoms_present': list(extracted_symptoms),
            'all_possible_diseases': list(disease_scores.keys()),
            'confidence': avg_confidence
        })
    
    except ValueError as e:
        return jsonify({'error': 'Invalid input format'}), 400
    except Exception as e:
        # Log full traceback for debugging
        logging.error('Diagnosis exception:\n%s', traceback.format_exc())
        return jsonify({'error': f'An error occurred during diagnosis. Please try again.'}), 500


@app.route('/api/diagnose_followup', methods=['POST'])
def diagnose_followup():
    """Handle follow-up answers and produce final recommendation"""
    try:
        data = request.json or {}
        answers = data.get('answers', {})
        disease = data.get('disease', None)
        age = data.get('age', None)

        # Simple logic: if any severe-answer keywords present, escalate
        severe_keywords = ['difficulty breathing', 'bleeding', 'chest pain', 'unconscious', 'severe pain']
        emergency = False
        yes_count = 0
        for q, a in answers.items():
            if not a:
                continue
            av = a.strip().lower()
            if av in ('yes', 'y', 'true', '1'):
                yes_count += 1
                for sk in severe_keywords:
                    if sk in q.lower():
                        emergency = True
        # Build final messages
        result_disease = disease or 'Unknown'
        description = description_list.get(result_disease, 'No description available')
        precautions = get_precautions_for_disease(result_disease)
        condition = 'Immediate medical attention recommended.' if emergency else 'Follow suggested precautions and consult a doctor if symptoms worsen.'
        result_message = f"Based on your answers, {'seek emergency care' if emergency else 'monitor symptoms and follow precautions'} for {result_disease}."

        return jsonify({
            'disease': result_disease,
            'description': description,
            'precautions': precautions,
            'condition': condition,
            'result_message': result_message
        })
    except Exception as e:
        logging.error('Followup error: %s', e)
        return jsonify({'error': 'Follow-up processing failed'}), 500

@app.route('/api/get_symptoms', methods=['GET'])
def get_symptoms():
    """Get all available symptoms"""
    return jsonify({'symptoms': list(chk_dis)})

@app.route('/api/health_qa', methods=['POST'])
def health_qa():
    """General health Q&A - answers any health-related question"""
    try:
        data = request.json or {}
        question = data.get('question', '').strip().lower()
        
        # Health knowledge base
        qa_database = {
            'fever': 'Fever is a body temperature above 98.6°F (37°C). It\'s usually a sign of infection. Rest, stay hydrated, and take paracetamol if needed. Consult a doctor if fever persists beyond 3 days.',
            'cough': 'Cough can be dry or productive (with mucus). Common causes: cold, flu, allergies. Remedies: drink water, honey tea, cough syrup. See doctor if it lasts more than 2 weeks.',
            'headache': 'Headaches can be tension, migraine, or cluster type. Relief: rest, hydration, pain relievers. Avoid stress and triggers. Consult doctor if severe or persistent.',
            'body pain': 'Body aches are muscle soreness often from flu, stress, or overexertion. Treatment: rest, warm compress, pain relief. Stretch gently and stay hydrated.',
            'sleep': 'Good sleep is 7-9 hours nightly. Tips: maintain schedule, avoid screens before bed, exercise daily, create dark cool room. Consult doctor for insomnia lasting weeks.',
            'exercise': 'Adults need 150 min moderate exercise weekly. Benefits: stronger heart, better mood, weight control. Start slow, warm up, cool down. Stay hydrated.',
            'diet': 'Healthy diet: 50% vegetables/fruits, 25% protein, 25% grains. Drink 8 glasses water daily. Limit sugar, salt, processed foods. Eat balanced meals.',
            'stress': 'Manage stress: meditation, yoga, deep breathing, exercise, hobbies. Limit caffeine, alcohol. Talk to someone. Chronic stress causes health issues - seek help.',
            'allergy': 'Allergies are immune overreactions. Symptoms: sneezing, itching, rash. Remedies: antihistamines, avoid triggers, keep area clean. See doctor for severe allergies.',
            'flu': 'Flu symptoms: fever, body ache, cough, weakness. Prevention: vaccine, hygiene, distance from sick. Treatment: rest, fluids. Consult doctor if severe.',
            'covid': 'COVID-19 symptoms: fever, cough, loss of taste/smell. Prevention: vaccine, mask, distance. Isolation if positive. Consult doctor if severe.',
            'diabetes': 'Diabetes: body can\'t regulate blood sugar. Type 1: genetic, needs insulin. Type 2: lifestyle-related, preventable. Monitor blood sugar, diet, exercise.',
            'blood pressure': 'Normal: <120/80. High BP increases heart disease risk. Reduce salt, exercise, manage stress. Medications available. Check regularly.',
            'cholesterol': 'Cholesterol types: HDL (good), LDL (bad). High LDL increases heart risk. Lower it: exercise, reduce saturated fats, eat fish, nuts.',
            'anxiety': 'Anxiety: excessive worry, panic attacks. Coping: breathing exercises, meditation, therapy, exercise. Medications available. Consult mental health professional.',
            'depression': 'Depression: persistent sadness, loss of interest. Seek help: therapy, counseling, medication. Exercise helps. Crisis: call hotline or go to ER.',
            'weight loss': 'Safe weight loss: 1-2 lbs weekly. Method: calorie deficit (diet + exercise). 80% diet, 20% exercise. Consult nutritionist for plans.',
            'weight gain': 'Healthy weight gain: 0.5-1 lb weekly. Eat calorie surplus + protein + strength training. Avoid junk. Consult nutritionist for plan.',
            'immunity': 'Boost immunity: vitamin C, D, sleep 8h, exercise, hygiene, manage stress, limit alcohol/smoking, balanced diet, probiotics.',
            'skin': 'Skin health: sunscreen SPF 30+, moisturize, cleanse gently, avoid harsh products, sleep well, hydrate. See dermatologist for persistent issues.',
            'hair': 'Hair health: protein-rich diet, scalp massage, limit heat styling, trim regularly, use quality shampoo. See doctor if unusual hair loss.',
            'dental': 'Dental health: brush 2x daily, floss daily, limit sugar, regular checkups. See dentist every 6 months. Whiten only under professional guidance.',
            'eye': 'Eye health: 20-20-20 rule (every 20 min, look 20ft for 20sec), UV protection, limit screen time, eat leafy greens. Eye exam yearly.',
            'pregnancy': 'Pregnancy: prenatal care essential. Avoid alcohol, smoking, raw foods. Take folic acid. Regular checkups. Healthy diet & exercise. Talk to OB/GYN.',
            'periods': 'Menstrual cycle: typically 28 days, 3-7 days bleeding. Normal: light to heavy flow. Irregular: consult doctor. PMS: exercise, diet, rest helps.',
            'vaccination': 'Vaccines prevent serious diseases. Schedule: childhood vaccines, flu yearly, boosters as needed. Safe, effective, minimal side effects.',
            'medicine': 'Take medicines as prescribed. Complete course even if better. Don\'t share medicines. Report side effects. Ask pharmacist about interactions.',
            'addiction': 'Addiction is treatable. Seek help: counseling, support groups, rehab. Prevention: avoid triggers, find healthy coping. Recovery is possible.',
            'doctor visit': 'Prepare: list symptoms, medications, questions. Be honest about habits. Discuss concerns. Get treatment plan. Follow up.',
            'emergency': 'Call 911 for: chest pain, difficulty breathing, severe bleeding, loss of consciousness, poisoning. Don\'t delay. Emergency care saves lives.',
        }
        
        # Find best matching answer
        best_match = None
        best_score = 0
        
        for keyword, answer in qa_database.items():
            if keyword in question:
                best_match = answer
                best_score = 100
                break
            elif any(word in question for word in keyword.split()):
                if len(keyword) > len(best_match or ''):
                    best_match = answer
                    best_score = 50
        
        if best_match:
            return jsonify({
                'answer': best_match,
                'type': 'health_qa'
            })
        else:
            # Generic health response
            return jsonify({
                'answer': 'General health tip: Maintain healthy lifestyle with balanced diet, regular exercise, 8 hours sleep, stress management, and regular health checkups. For specific medical concerns, consult a healthcare professional.',
                'type': 'health_qa'
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/download_report', methods=['POST'])
def download_report():
    """Return a downloadable health report as a PDF built from diagnosis JSON."""
    try:
        data = request.json or {}
        diagnosis = data.get('diagnosis', {})
        input_text = data.get('input_text', '')
        treatments = diagnosis.get('treatments', []) or []

        now_dt = datetime.datetime.now()
        now = now_dt.strftime('%Y-%m-%d %H:%M:%S')
        timestamp = now_dt.strftime('%Y%m%d_%H%M%S')

        # Patient info (optional)
        patient_name = (data.get('patient_name') or '').strip()
        patient_age = data.get('age', '')

        # Logo path (optional) - check static/logo.png
        logo_path = os.path.join(BASE_DIR, 'static', 'logo.png')
        logo_exists = os.path.exists(logo_path)

        # If reportlab is available, create PDF in memory, otherwise fallback to plain text
        if HAVE_REPORTLAB:
            # Try to use Platypus for nicer PDF formatting; fall back to canvas if platypus not available
            try:
                platypus = importlib.import_module('reportlab.platypus')
                styles_mod = importlib.import_module('reportlab.lib.styles')
                table_mod = importlib.import_module('reportlab.platypus.tables')
                enums = importlib.import_module('reportlab.lib.enums')

                SimpleDocTemplate = getattr(platypus, 'SimpleDocTemplate')
                Paragraph = getattr(platypus, 'Paragraph')
                Spacer = getattr(platypus, 'Spacer')
                Table = getattr(table_mod, 'Table')
                TableStyle = getattr(table_mod, 'TableStyle')

                getSampleStyleSheet = getattr(styles_mod, 'getSampleStyleSheet')
                ParagraphStyle = getattr(styles_mod, 'ParagraphStyle')

                styles = getSampleStyleSheet()
                title_style = ParagraphStyle(
                    'TitleStyle', parent=styles['Title'], fontSize=18, leading=22, spaceAfter=12
                )
                heading_style = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=12, leading=14, spaceAfter=6)
                normal_style = ParagraphStyle('Normal', parent=styles['Normal'], fontSize=10, leading=13)

                buffer = io.BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=inch, leftMargin=inch, topMargin=inch, bottomMargin=inch)
                elements = []

                # Title and metadata (include patient info when available)
                # If a logo exists, try to include it above the title
                if logo_exists:
                    try:
                        Image = getattr(platypus, 'Image')
                        img = Image(logo_path, width=60, height=60)
                        elements.append(img)
                    except Exception:
                        pass
                elements.append(Paragraph(f"{CHATBOT_NAME} - Health Report", title_style))
                metadata = [
                    ['Date:', now],
                    ['Patient:', patient_name or 'N/A'],
                    ['Age:', str(patient_age) or 'N/A'],
                    ['Primary Disease:', diagnosis.get('disease', 'N/A')],
                    ['Confidence:', f"{round(diagnosis.get('confidence', 0) * 100, 2)}%" if isinstance(diagnosis.get('confidence', 0), (int, float)) else str(diagnosis.get('confidence', '0'))]
                ]
                table = Table(metadata, colWidths=[110, 350])
                table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ]))
                elements.append(table)
                elements.append(Spacer(1, 8))

                # Input text
                if input_text:
                    elements.append(Paragraph('<b>Input:</b>', heading_style))
                    elements.append(Paragraph(input_text, normal_style))
                    elements.append(Spacer(1, 6))

                # Description
                elements.append(Paragraph('<b>Description</b>', heading_style))
                elements.append(Paragraph(diagnosis.get('description', 'No description available'), normal_style))
                elements.append(Spacer(1, 8))

                # Precautions
                elements.append(Paragraph('<b>Precautions</b>', heading_style))
                precautions = diagnosis.get('precautions', []) or []
                if precautions:
                    for p in precautions:
                        elements.append(Paragraph(f'• {p}', normal_style))
                else:
                    elements.append(Paragraph('• Follow up with a healthcare professional', normal_style))
                elements.append(Spacer(1, 8))

                # Common Treatments
                elements.append(Paragraph('<b>Common Treatments</b>', heading_style))
                if not treatments:
                    derived = derive_common_treatments(diagnosis.get('disease'))
                    if derived:
                        treatments = derived

                if treatments:
                    for t in treatments:
                        elements.append(Paragraph(f'• {t}', normal_style))
                else:
                    elements.append(Paragraph('• None specified', normal_style))
                elements.append(Spacer(1, 8))

                # All possible diseases
                elements.append(Paragraph('<b>All Possible Diseases</b>', heading_style))
                elements.append(Paragraph(', '.join(diagnosis.get('all_possible_diseases', [])), normal_style))

                # Build PDF
                doc.build(elements)
                buffer.seek(0)
                safe_name = re.sub(r'[^0-9A-Za-z_-]', '', (patient_name or 'patient').replace(' ', '_'))
                filename = f"{CHATBOT_NAME}_{safe_name}_{timestamp}.pdf"
                return send_file(buffer, as_attachment=True, download_name=filename, mimetype='application/pdf')
            except Exception:
                # If Platypus isn't available or errors, fall back to canvas approach used previously
                try:
                    buffer = io.BytesIO()
                    pdf = canvas.Canvas(buffer, pagesize=letter)
                    width, height = letter

                    margin = 0.7 * inch
                    x = margin
                    y = height - margin

                    # Draw logo (if exists) at top-left
                    if logo_exists:
                        try:
                            pdf.drawImage(logo_path, x, y - 60, width=60, height=60)
                        except Exception:
                            pass

                    pdf.setFont('Helvetica-Bold', 16)
                    pdf.drawString(x + (70 if logo_exists else 0), y, f"{CHATBOT_NAME} - Health Report")
                    y -= 20
                    pdf.setFont('Helvetica', 9)
                    pdf.drawString(x + (70 if logo_exists else 0), y, f'Date: {now}')
                    y -= 14
                    # Patient details
                    if patient_name:
                        pdf.setFont('Helvetica', 10)
                        pdf.drawString(x + (70 if logo_exists else 0), y, f'Patient: {patient_name}    Age: {patient_age}')
                        y -= 14

                    if input_text:
                        pdf.setFont('Helvetica-Bold', 11)
                        pdf.drawString(x, y, 'Input:')
                        y -= 12
                        pdf.setFont('Helvetica', 10)
                        text = pdf.beginText(x, y)
                        for line in split_text(input_text, 80):
                            text.textLine(line)
                            y -= 12
                        pdf.drawText(text)
                        y -= 6

                    pdf.setFont('Helvetica-Bold', 11)
                    pdf.drawString(x, y, 'Primary Disease:')
                    pdf.setFont('Helvetica', 11)
                    pdf.drawString(x + 110, y, diagnosis.get('disease', 'N/A'))
                    y -= 16

                    pdf.setFont('Helvetica-Bold', 11)
                    pdf.drawString(x, y, 'Confidence:')
                    conf = diagnosis.get('confidence', 0)
                    try:
                        conf_pct = f"{round(conf * 100, 2)}%"
                    except Exception:
                        conf_pct = str(conf)
                    pdf.setFont('Helvetica', 11)
                    pdf.drawString(x + 110, y, conf_pct)
                    y -= 18

                    pdf.setFont('Helvetica-Bold', 11)
                    pdf.drawString(x, y, 'Symptoms Present:')
                    pdf.setFont('Helvetica', 10)
                    symptoms = diagnosis.get('symptoms_present', []) or []
                    pdf.drawString(x + 130, y, ', '.join(symptoms) if symptoms else 'N/A')
                    y -= 18

                    pdf.setFont('Helvetica-Bold', 11)
                    pdf.drawString(x, y, 'Description:')
                    y -= 12
                    pdf.setFont('Helvetica', 10)
                    text = pdf.beginText(x, y)
                    for line in split_text(diagnosis.get('description', 'No description available'), 90):
                        text.textLine(line)
                        y -= 12
                    pdf.drawText(text)
                    y -= 8

                    pdf.setFont('Helvetica-Bold', 11)
                    pdf.drawString(x, y, 'Precautions:')
                    y -= 12
                    pdf.setFont('Helvetica', 10)
                    precautions = diagnosis.get('precautions', []) or []
                    if precautions:
                        for p in precautions:
                            pdf.drawString(x + 8, y, f'- {p}')
                            y -= 12
                    else:
                        pdf.drawString(x + 8, y, '- Follow up with a healthcare professional')
                        y -= 12

                    y -= 6
                    pdf.setFont('Helvetica-Bold', 11)
                    pdf.drawString(x, y, 'Common Treatments:')
                    y -= 12
                    pdf.setFont('Helvetica', 10)
                    if not treatments:
                        derived = derive_common_treatments(diagnosis.get('disease'))
                        if derived:
                            treatments = derived

                    if treatments:
                        for m in treatments:
                            pdf.drawString(x + 8, y, f'- {m}')
                            y -= 12
                    else:
                        pdf.drawString(x + 8, y, '- None specified')
                        y -= 12

                    y -= 6
                    pdf.setFont('Helvetica-Bold', 11)
                    pdf.drawString(x, y, 'All Possible Diseases:')
                    y -= 12
                    pdf.setFont('Helvetica', 10)
                    pdf.drawString(x + 8, y, ', '.join(diagnosis.get('all_possible_diseases', [])))
                    y -= 18

                    pdf.showPage()
                    pdf.save()
                    buffer.seek(0)
                    safe_name = re.sub(r'[^0-9A-Za-z_-]', '', (patient_name or 'patient').replace(' ', '_'))
                    filename = f"{CHATBOT_NAME}_{safe_name}_{timestamp}.pdf"
                    return send_file(buffer, as_attachment=True, download_name=filename, mimetype='application/pdf')
                except Exception as e:
                    logging.error('Fallback PDF generation failed: %s', e)
                    return jsonify({'error': 'Failed to generate PDF report'}), 500
        else:
            # PDF generation is required for this endpoint. Inform the client to install reportlab.
            msg = (
                'PDF generation is not available on the server. To enable PDF reports, '
                'install ReportLab in the server environment: `pip install reportlab`.'
            )
            logging.error(msg)
            return jsonify({'error': msg}), 501
    except Exception as e:
        logging.error('Report generation failed: %s', e)
        return jsonify({'error': 'Failed to generate report'}), 500


def split_text(text, width):
    """Helper to split long text into chunks for PDF lines."""
    if not text:
        return ['']
    words = text.split()
    lines = []
    current = ''
    for w in words:
        if len(current) + len(w) + 1 <= width:
            current = (current + ' ' + w).strip()
        else:
            lines.append(current)
            current = w
    if current:
        lines.append(current)
    return lines

if __name__ == '__main__':
    logging.info('HealthCare ChatBot Starting...')
    logging.info('Open your browser and go to: http://localhost:5000')
    app.run(debug=True, port=5000)
