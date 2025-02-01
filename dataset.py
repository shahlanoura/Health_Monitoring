from flask import Flask, render_template, jsonify
import pandas as pd
import random
from datetime import datetime

app = Flask(__name__)

# Load glucose data from CSV and clean column names
df = pd.read_csv("glucose_data.csv")
df.columns = df.columns.str.strip().str.lower()  # Standardize column names

# Ensure the ID column starts from 1001 if not already present
if "id" not in df.columns:
    df.insert(0, "id", range(1001, 1001 + len(df)))

# Convert systemTime to datetime format
df["systemtime"] = pd.to_datetime(df["systemtime"])

# Generate patient data
def generate_patient_data():
    patients = []

    for _, row in df.iterrows():
        patient = {
            "id": row["id"], 
            "name": f"Patient {row['id']}",
            "condition": "Diabetes" if row["value"] > 100 else "Hypertension",  
            "glucose_level": row["value"],  
            "bp": (random.randint(100, 160), random.randint(60, 100)),
            "last_update": row["systemtime"].strftime("%Y-%m-%d %H:%M:%S")
        }
        patients.append(patient)

    alerts = []
    for patient in patients:
        alert_msg = None
        if patient["glucose_level"] < 70:
            alert_msg = f"Low glucose alert for {patient['name']} ({patient['glucose_level']} mg/dL)"
        elif patient["glucose_level"] > 180:
            alert_msg = f"High glucose alert for {patient['name']} ({patient['glucose_level']} mg/dL)"

        if patient["bp"][0] > 140 or patient["bp"][1] > 90:
            alert_msg = f"High BP alert for {patient['name']} ({patient['bp'][0]}/{patient['bp'][1]} mmHg)"

        if alert_msg:
            alerts.append({"patient": patient["name"], "message": alert_msg, "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})

    return {"patients": patients, "alerts": alerts}

@app.route('/')
def index():
    return render_template('ind.html')

@app.route('/get_alerts')
def get_alerts():
    data = generate_patient_data()
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)
