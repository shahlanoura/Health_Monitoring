from flask import Flask, request, redirect, jsonify, render_template, session
import requests
from datetime import datetime, timezone
import csv
import os
import pandas as pd
from urllib.parse import quote
app = Flask(__name__)

app.secret_key = os.urandom(24)

# Dexcom API credentials
client_id = "tbRbOM8IyjxLxZghtcqVsYJ6tNhsZ5Lb"
client_secret = "RGHyxzyb60SKBhIc"
redirect_uri = "http://localhost:5000/callback"

# Step 1: Redirect to Dexcom OAuth2 for authorization
@app.route('/')
def index():
    return render_template("index.html")

@app.route('/dates', methods=['GET', 'POST'])
def dates():
    if request.method == 'POST':
        start_date_str = request.form['start_date']
        end_date_str = request.form['end_date']
        
        # Encode dates in the state parameter
        state = quote(f"start_date={start_date_str}&end_date={end_date_str}")
        
        # Redirect to Dexcom OAuth2 login URL
        authorization_url = (
            f"https://sandbox-api.dexcom.com/v2/oauth2/login"
            f"?response_type=code"
            f"&client_id={client_id}"
            f"&redirect_uri={redirect_uri}"
            f"&state={state}"
        )
        return redirect(authorization_url)
    
    return render_template("dates.html")

@app.route('/callback')
def callback():
    auth_code = request.args.get('code')
    state = request.args.get('state')
    
    if not auth_code or not state:
        return "Error: Authorization code or state missing."

    # Decode the state parameter
    state_params = parse_qs(unquote(state))
    start_date_str = state_params.get('start_date', [None])[0]
    end_date_str = state_params.get('end_date', [None])[0]
    
    if not start_date_str or not end_date_str:
        return "Error: Date range missing."

    # Ensure the dates are in the correct format
    try:
        start_date = datetime.fromisoformat(start_date_str).astimezone(timezone.utc)
        end_date = datetime.fromisoformat(end_date_str).astimezone(timezone.utc)
    except ValueError:
        return "Error: Invalid date format. Please use YYYY-MM-DDTHH:mm:ss."

    start_date_str = start_date.strftime('%Y-%m-%dT%H:%M:%S')
    end_date_str = end_date.strftime('%Y-%m-%dT%H:%M:%S')

    access_token = get_access_token(auth_code)
    if access_token:
        glucose_data = fetch_glucose_data(access_token, start_date_str, end_date_str)
        if glucose_data:
            if "egvs" in glucose_data and glucose_data["egvs"]:
                glucose_df = convert_to_dataframe(glucose_data["egvs"])
                alerts = glucose_alert(glucose_df)
                return render_template("table.html", glucose_data=glucose_df.to_html(classes='data', header=True), alerts=alerts)
            else:
                return "No glucose data available for the specified date range."
        else:
            return "Error: Failed to fetch glucose data."
    else:
        return "Error: Failed to fetch access token."

# Step 3: Exchange authorization code for access token
def get_access_token(auth_code):
    token_url = "https://sandbox-api.dexcom.com/v2/oauth2/token"
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": auth_code,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }
    response = requests.post(token_url, data=payload)
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        error_message = response.json().get("error", "Unknown error")
        print(f"Failed to fetch access token: {error_message}")
        return None

# Step 4: Fetch glucose data
def fetch_glucose_data(access_token, start_date_str, end_date_str):
    url = "https://sandbox-api.dexcom.com/v2/users/self/egvs"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"startDate": start_date_str, "endDate": end_date_str}
    response = requests.get(url, headers=headers, params=params)
    print(f"Response Status Code: {response.status_code}")
    print(f"Response Content: {response.text}")
    if response.status_code == 200:
        return response.json()
    else:
        print("Failed to fetch glucose data:", response.json())
        return None

def convert_to_dataframe(data):
    import pandas as pd

    # Create a DataFrame
    df = pd.DataFrame(data)
    
    # Display first few rows
    print(df.head())
    
    # Handle missing values
    df.isnull().sum()
    df.ffill(inplace=True)

    # Convert time columns to datetime
    df['systemTime'] = pd.to_datetime(df['systemTime'])
    df['displayTime'] = pd.to_datetime(df['displayTime'])

    # Add additional time-based columns
    df['year'] = df['systemTime'].dt.year
    df['day'] = df['systemTime'].dt.day
    df['hour'] = df['systemTime'].dt.hour
    df['minute'] = df['systemTime'].dt.minute
    df['second'] = df['systemTime'].dt.second

    # Save DataFrame to a CSV file
    df.to_csv('glucose_data.csv', index=False)

    return df

def glucose_alert(df):
    # Define thresholds
    low_threshold = 70
    high_threshold = 180
    rapid_change_threshold = 0.5

    # Initialize an empty list for alerts
    alerts = []

    # Iterate through the DataFrame
    for index, row in df.iterrows():
        if row['value'] < low_threshold:
            alerts.append(f"Low Glucose Alert at {row['systemTime']}: Glucose value is {row['value']}.")
        elif row['value'] > high_threshold:
            alerts.append(f"High Glucose Alert at {row['systemTime']}: Glucose value is {row['value']}.")
        
        if row['trendRate'] > rapid_change_threshold:
            alerts.append(f"Rapid Glucose Increase Alert at {row['systemTime']}: Trend rate is {row['trendRate']}.")
        elif row['trendRate'] < -rapid_change_threshold:
            alerts.append(f"Rapid Glucose Drop Alert at {row['systemTime']}: Trend rate is {row['trendRate']}.")

    return alerts

if __name__ == '__main__':
    app.run(debug=True)