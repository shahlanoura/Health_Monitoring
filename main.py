from flask import Flask, request, redirect, jsonify, render_template
import requests
from datetime import datetime, timezone
import csv
import os
import pandas as pd
from datetime import datetime, timedelta, timezone


current_date = datetime.now(timezone.utc)

# Calculate the date range for the last week
start_date = current_date - timedelta(days=30)
end_date = current_date

# Format the datetime objects without timezone information
start_date_str = start_date.strftime('%Y-%m-%dT%H:%M:%S')
end_date_str = end_date.strftime('%Y-%m-%dT%H:%M:%S')

print(f"Start Date: {start_date_str}, End Date: {end_date_str}")

app = Flask(__name__)

# Dexcom API credentials
client_id = "tbRbOM8IyjxLxZghtcqVsYJ6tNhsZ5Lb"
client_secret = "RGHyxzyb60SKBhIc"
redirect_uri = "http://localhost:5000/callback"

# Step 1: Redirect to Dexcom OAuth2 for authorization
@app.route('/')
def index():
    authorization_url = (
        f"https://sandbox-api.dexcom.com/v2/oauth2/login"
        f"?response_type=code"
        f"&client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
    )
    return redirect(authorization_url)



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
        print(f"Response content: {response.text}")

        return None
@app.route('/callback')
def callback():
    auth_code = request.args.get('code')
    if not auth_code:
        return "Error: Authorization code missing."

    access_token = get_access_token(auth_code)
    if access_token:
        glucose_data = fetch_glucose_data(access_token, start_date_str, end_date_str)
        if glucose_data:
            
            if "egvs" in glucose_data and glucose_data["egvs"]:
                glucose_df = convert_to_dataframe(glucose_data["egvs"])
            
                return render_template("table.html", glucose_data=glucose_df.to_html(classes='data', header=True))
            else:
                return "No glucose data available for the specified date range."
        else:
            return "Error: Failed to fetch glucose data."
    else:
        return "Error: Failed to fetch access token."
def convert_to_dataframe(data):
    import pandas as pd
    df = pd.DataFrame(data)
    df.ffill(inplace=True)
    

    
    df.to_csv('glucose_data.csv', index=False)

    return df


if __name__ == '__main__':
    app.run(debug=True)
