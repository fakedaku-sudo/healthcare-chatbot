from flask import Flask, render_template, request, jsonify
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
import warnings
import traceback

warnings.filterwarnings("ignore", category=DeprecationWarning)

app = Flask(__name__)

# ==================== DATA LOADING ====================
print("[Loading Data...]")
training = pd.read_csv('Training.csv')
testing = pd.read_csv('Testing.csv')
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
print(scores.mean())

model = SVC()
model.fit(x_train, y_train)
print("for svm: ")
print(model.score(x_test, y_test))

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

# ==================== HELPER FUNCTIONS ====================

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
    with open('symptom_Description.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            _description = {row[0]: row[1]}
            description_list.update(_description)

def getSeverityDict():
    """Load symptom severity data from CSV"""
    global severityDictionary
    with open('Symptom_severity.csv') as csv_file:
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
    with open('symptom_precaution.csv') as csv_file:
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
    df = pd.read_csv('Training.csv')
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
                    return jsonify({
                        'disease': result_disease,
                        'description': description,
                        'precautions': precautions,
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
            'result_message': result_msg,
            'symptoms_present': list(extracted_symptoms),
            'all_possible_diseases': list(disease_scores.keys()),
            'confidence': avg_confidence
        })
    
    except ValueError as e:
        return jsonify({'error': 'Invalid input format'}), 400
    except Exception as e:
        # Print full traceback for debugging
        print("[ERROR] Diagnosis exception:\n" + traceback.format_exc())
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
        print(f"[ERROR] Followup error: {e}")
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

if __name__ == '__main__':
    print("[INFO] HealthCare ChatBot Starting...")
    print("[INFO] Open your browser and go to: http://localhost:5000")
    app.run(debug=True, port=5000)
