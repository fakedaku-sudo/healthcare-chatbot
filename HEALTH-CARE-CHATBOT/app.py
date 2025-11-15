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
        for row in csv_reader:
            _prec = {row[0]: [row[1], row[2], row[3], row[4]]}
            precautionDictionary.update(_prec)

def calc_condition(exp, days):
    """Calculate severity condition"""
    sum_val = 0
    for item in exp:
        sum_val = sum_val + severityDictionary[item]
    
    if ((sum_val * days) / (len(exp) + 1) > 13):
        return "You should take the consultation from doctor."
    else:
        return "It might not be that bad but you should take precautions."

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
        disease_input = data.get('symptom', '').strip()
        num_days = int(data.get('days', 1))
        age = data.get('age', None)
        known = data.get('known_disease', '').strip()

        # Accept either symptom or known disease
        if known:
            disease_input = known

        if not disease_input:
            return jsonify({'error': 'Please enter a symptom or disease'}), 400

        # Check if input matches a symptom
        conf, cnf_dis = check_pattern(chk_dis, disease_input)
        if conf == 1 and cnf_dis:
            # Use the first matching symptom
            disease_input = cnf_dis[0]
            input_is_disease = False
        else:
            # try matching disease names
            input_is_disease = False
            try:
                matches = [d for d in le.classes_ if disease_input.lower() in d.lower()]
                if matches:
                    # treat the first matched disease as the disease
                    result_disease = matches[0]
                    input_is_disease = True
                else:
                    return jsonify({'error': 'Enter valid symptom or disease'}), 400
            except Exception:
                return jsonify({'error': 'Enter valid symptom or disease'}), 400

        # If user provided disease directly, skip tree traversal and prepare followups
        if input_is_disease:
            chosen = result_disease
            followups = []
            disease_followups = {
                'dengue': ['Do you have severe body pain (yes/no)?', 'Do you have bleeding or bruising (yes/no)?', 'Have you noticed a rash (yes/no)?'],
                'malaria': ['Do you have chills and high fever (yes/no)?', 'Do you have sweating episodes (yes/no)?'],
                'influenza': ['Do you have sore throat (yes/no)?', 'Do you have muscle aches (yes/no)?'],
                'covid-19': ['Do you have difficulty breathing (yes/no)?', 'Do you have loss of taste or smell (yes/no)?'],
                'hypertension': ['Do you have frequent headaches (yes/no)?', 'Any chest pain (yes/no)?'],
                'diabetes': ['Do you have increased thirst or urination (yes/no)?', 'Any slow-healing wounds (yes/no)?']
            }
            key = chosen.lower()
            if key in disease_followups:
                followups = disease_followups[key]
            else:
                # generic followups based on age
                if age is not None:
                    try:
                        agev = int(age)
                        if agev < 12:
                            followups = ['Is there poor feeding or persistent vomiting (yes/no)?', 'Is the child unusually drowsy (yes/no)?']
                        elif agev >= 65:
                            followups = ['Any recent falls or confusion (yes/no)?', 'Are you having difficulty breathing (yes/no)?']
                        else:
                            followups = ['Do you have fever (yes/no)?', 'Are you experiencing severe pain (yes/no)?']
                    except Exception:
                        followups = ['Do you have fever (yes/no)?', 'Are you experiencing severe pain (yes/no)?']
                else:
                    followups = ['Do you have fever (yes/no)?', 'Are you experiencing severe pain (yes/no)?']

            return jsonify({'followup': followups, 'disease': chosen})

        # ==================== TREE TRAVERSAL (from chat_bot.py) ====================
        tree_ = clf.tree_
        feature_name = [
            cols[i] if i != _tree.TREE_UNDEFINED else "undefined!"
            for i in tree_.feature
        ]

        symptoms_present = []
        present_disease = None
        symptoms_given = []

        def recurse(node, depth):
            nonlocal present_disease, symptoms_given, symptoms_present

            indent = "  " * depth
            if tree_.feature[node] != _tree.TREE_UNDEFINED:
                name = feature_name[node]
                threshold = tree_.threshold[node]

                if name == disease_input:
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
                red_cols = reduced_data.columns
                symptoms_given = list(red_cols[reduced_data.loc[present_disease].values[0].nonzero()])

        # Start tree traversal
        recurse(0, 1)
        
        # Get secondary prediction
        second_prediction = sec_predict(symptoms_present)
        condition_msg = calc_condition(symptoms_present, num_days)
        
        # Determine final disease
        result_disease = present_disease[0] if present_disease else "Unknown"
        
        description = description_list.get(result_disease, "No description available")
        precautions = precautionDictionary.get(result_disease, [])
        
        # Check if primary and secondary predictions match (from chat_bot.py logic)
        if (present_disease[0] == second_prediction[0]):
            final_result = f"You may have {present_disease[0]}"
        else:
            final_result = f"You may have {present_disease[0]} or {second_prediction[0]}"
        
        return jsonify({
            'disease': result_disease,
            'description': description,
            'condition': condition_msg,
            'precautions': precautions,
            'result_message': final_result,
            'symptoms_present': symptoms_present,
            'confidence': len(symptoms_present) / max(len(symptoms_given), 1) if symptoms_given else 0
        })
    
    except ValueError as e:
        return jsonify({'error': 'Invalid input format'}), 400
    except Exception as e:
        print(f"[ERROR] Diagnosis error: {e}")
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500


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
        precautions = precautionDictionary.get(result_disease, [])
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
