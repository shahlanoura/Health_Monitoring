import pandas as pd
import joblib
from flask import Flask, render_template, jsonify
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import LabelEncoder


app = Flask(__name__)


data_path = "D:/Heath_Care/BP_data.joblib"
df_bp = joblib.load(data_path)  
df = pd.read_csv("glucose_data.csv")

df.rename(columns={"value": "Glucose"}, inplace=True)
df.drop(columns=['systemTime','displayTime','status'],axis=1,inplace=True)
df2=pd.concat([df,df_bp],axis=1).dropna()

df2 = pd.merge(df, df_bp, left_index=True, right_index=True, how='inner')
df2.insert(0, 'id', range(1001, 1001 + len(df2)))

df2[['Systolic_blood_pressure', 'Diastolic_blood_pressure']] = df2['blood_pressure'].str.split('/', expand=True).astype(float)


def diabetes_risk(row):
    if row['Glucose'] >= 126:  
        return 1
    elif row['Systolic_blood_pressure'] >= 140 or row['Diastolic_blood_pressure'] >= 90:  
        return 1
    elif row['Systolic_blood_pressure'] <= 90 or row['Diastolic_blood_pressure'] <= 60:  
        return 1
    elif row['HeartRate'] < 60 or row['HeartRate'] > 100:  
        return 1
    else:
        return 0  

# Apply function
df2['diabetes'] = df2.apply(diabetes_risk, axis=1)
print(df2['diabetes'].value_counts())


label_encoder = LabelEncoder()
df2['trend'] = label_encoder.fit_transform(df2['trend'])  

print(df2.head())
X=df2.drop(columns=['diabetes','blood_pressure'])
y=df2['diabetes']
X_train,X_test,y_train,y_test=train_test_split(X,y,train_size=0.8)
model=RandomForestClassifier()
model.fit(X_train,y_train)
y_pred=model.predict(X_test)
Model_score=accuracy_score(y_test,y_pred)
print(Model_score)
def generate_alerts():
    alerts = []
    for _, row in df2.iterrows():
        patient_id = row["id"]
        patient_name = f"Patient {patient_id}"
        glucose_level = row.get("Glucose", None)  
        blood_pressure1 = row.get("Systolic_blood_pressure", "N/A")
        blood_pressure2 = row.get("Diastolic_blood_pressure", "N/A")
        heart_rate = row.get("HeartRate", "N/A")  

        
        if pd.isna(glucose_level) or not isinstance(glucose_level, (int, float)):
            continue 

        
        if glucose_level < 70 or glucose_level > 200:
            alert_message = (
                f"⚠️ {'Low' if glucose_level < 70 else 'High'} glucose alert ({glucose_level} mg/dL)\n"
                f"🩺 Blood Pressure: {blood_pressure1}/{blood_pressure2}\n"
                f"💓 Heart Rate: {heart_rate} bpm"
            )
            alerts.append({
                "id": int(patient_id),
                "patient": patient_name,
                "message": alert_message,
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

    return {"alerts": alerts}


def fetch_patient_details(patient_id):
    patient_data = df2[df2["id"] == patient_id]
    if patient_data.empty:
        return {"error": "Patient not found"}
    
    patient_info = patient_data.iloc[-1]

    
    timestamp = (
        patient_info["systemtime"].strftime("%Y-%m-%d %H:%M:%S")
        if "systemtime" in patient_info and pd.notna(patient_info["systemtime"])
        else "N/A"
    )

    return {
        "name": f"Patient {int(patient_id)}",
        "glucose_level": float(patient_info["value"]),
        "condition": "Critical" if patient_info["value"] < 70 or patient_info["value"] > 200 else "Stable",
        "heart_rate": patient_info.get("heart_rate", "N/A"),
        "blood_pressure": patient_info.get("blood_pressure", "N/A"),
        "timestamp": timestamp
    }


@app.route('/')
def index():
    return render_template('ind.html')

@app.route('/get_alerts')
def get_alerts():
    return jsonify(generate_alerts())

@app.route('/get_patient_details/<int:patient_id>')
def get_patient_details_route(patient_id):
    return jsonify(fetch_patient_details(patient_id))

if __name__ == '__main__':
    app.run(debug=True)
