# Health_Monitoring
 Health Monitoring System Documentation

 Overview
The **Health Monitoring System** is designed to collect, analyze, and provide alerts based on a patient's health parameters such as glucose levels and blood pressure. The system integrates with Dexcom API for glucose data and uses predictive analytics for health monitoring.

 Features
- Fetches real-time glucose data from **Dexcom API**.
- Processes **blood pressure** readings.
- Merges health data into a unified dataset.
- Predicts health trends using **machine learning models**.
- Generates alerts based on critical health parameters.
- Provides an API interface for external access.

System Architecture
The system consists of the following modules:

 1. Data Collection Module
- `main.py`: Fetches glucose data from Dexcom API.
- `dataset.py`: Processes and merges health data.

 2. Data Processing Module
- Glucose Data Processing: Retrieves real-time glucose readings.
- Blood Pressure Processing: Extracts systolic and diastolic values from stored readings.

3. Prediction & Alerting Module
- Uses machine learning models to predict abnormal trends.
- Triggers alerts if values exceed defined thresholds.

4. API Interface
- Exposes RESTful APIs for external applications to fetch health data and alerts.
 Installation
Prerequisites
- Python 3.11+
- Dexcom API access
- Libraries: Install using `requirements.txt`

```bash
pip install -r requirements.txt
```

Usage
1. Run the Data Collection Service
```bash
python main.py
```
This fetches glucose data from the Dexcom API.

2. Process the Dataset 
```bash
python dataset.py
```
This merges glucose and blood pressure data for analysis.

3. Run the API Server
```bash
uvicorn api:app --reload
```
This starts the REST API for external access.

API Endpoints
1. Get Patient Data
```http
GET /api/patient/{patient_id}
```
Response:
```json
{
  "timestamp": "2024-02-09 10:00:00",
  "glucose_level": 110,
  "blood_pressure": "120/80"
}
```

2. Get Alerts
```http
GET /api/alerts
```
Response:
```json
{
  "alerts": [
    "Glucose level too high: 250 mg/dL",
    "Blood pressure too high: 140/90"
  ]
}
```

Error Handling
- Missing API credentials → `401 Unauthorized`
- Data not found → `404 Not Found`
- Server error → `500 Internal Server Error`
Future Enhancements
- **AI-driven health recommendations**.
- **Integration with wearable devices**.
- **Personalized notifications**.



