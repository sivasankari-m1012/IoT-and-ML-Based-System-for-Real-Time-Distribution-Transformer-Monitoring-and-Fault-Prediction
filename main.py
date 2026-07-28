from flask import Flask, request, jsonify, render_template
import pandas as pd
import os
from datetime import datetime
import joblib

# ---------------- INIT ----------------
app = Flask(__name__)

# ---------------- PATHS ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

file_path = os.path.join(BASE_DIR, "data.csv")
model_path = os.path.join(BASE_DIR, "model.pkl")

# ---------------- LOAD MODEL ----------------
model = joblib.load(model_path)

# ---------------- SAFE FLOAT ----------------
def safe_float(value):
    try:
        return float(value)
    except:
        return 0.0

# ---------------- HOME ----------------
@app.route('/')
def home():
    return "Flask Server Running ✅"

# ---------------- DASHBOARD ----------------
@app.route('/dashboard')
def dashboard():

    try:

        # -------- CHECK IF CSV EXISTS --------
        if not os.path.exists(file_path):
            return "No data yet. Waiting for sensor readings..."

        # -------- READ CSV --------
        df = pd.read_csv(file_path)

        if len(df) == 0:
            return "CSV file is empty. Waiting for sensor readings..."

        # -------- LATEST ROW (for the 4 cards + status) --------
        latest = df.iloc[-1]

        # -------- FULL HISTORY (for the graph) --------
        # .tolist() converts pandas columns into plain Python lists
        # so Chart.js (JavaScript) can read them as JSON arrays
        time_data = df["Time"].astype(str).tolist()
        voltage_data = df["Voltage"].tolist()
        current_data = df["Current"].tolist()
        temp_data = df["Temperature"].tolist()

        # -------- ALERTS (same thresholds as the Streamlit version) --------
        high_temp_alert = latest['Temperature'] > 60
        low_voltage_alert = latest['Voltage'] < 5
        low_oil_alert = latest['Oil_Percentage'] < 20

        # -------- LAST 10 ROWS (for the table, newest first) --------
        last_10 = df.tail(10).iloc[::-1].to_dict(orient='records')

        # -------- RENDER TEMPLATE --------
        # render_template looks for dashboard.html inside the "templates" folder
        # and fills {{ temp }}, {{ voltage }}, etc. with these real values
        return render_template(
            'dashboard.html',
            temp=latest['Temperature'],
            voltage=latest['Voltage'],
            current=latest['Current'],
            oil=latest['Oil_Percentage'],
            status=latest['Status'],
            time_data=time_data,
            voltage_data=voltage_data,
            current_data=current_data,
            temp_data=temp_data,
            high_temp_alert=high_temp_alert,
            low_voltage_alert=low_voltage_alert,
            low_oil_alert=low_oil_alert,
            last_10=last_10
        )

    except Exception as e:

        print("DASHBOARD ERROR:", e)
        return f"Error loading dashboard: {e}", 500


# ---------------- DATA API ----------------
@app.route('/data')
def data():

    try:

        # -------- RECEIVE ESP VALUES --------
        temp = safe_float(request.args.get('temp'))
        voltage = safe_float(request.args.get('voltage'))
        current = safe_float(request.args.get('current'))
        oil_distance = safe_float(request.args.get('oil'))

        # -------- OIL % --------
        tank_height = 30

        if oil_distance <= 0 or oil_distance > tank_height:
            oil_percent = 0
        else:
            oil_percent = ((tank_height - oil_distance) / tank_height) * 100

        oil_percent = max(0, min(100, oil_percent))

        # -------- ML PREDICTION --------
        input_df = pd.DataFrame(
            [[temp, voltage, current, oil_percent]],
            columns=[
                "Temperature",
                "Voltage",
                "Current",
                "Oil_Percentage"
            ]
        )

        prediction = model.predict(input_df)

        status = prediction[0]

        print(
            "DATA:",
            temp,
            voltage,
            current,
            oil_percent,
            "→",
            status
        )

        # -------- SAVE CSV --------
        new_data = pd.DataFrame([{
            "Time": datetime.now(),
            "Temperature": temp,
            "Voltage": voltage,
            "Current": current,
            "Oil_Percentage": oil_percent,
            "Status": status
        }])

        if os.path.exists(file_path):

            new_data.to_csv(
                file_path,
                mode='a',
                header=False,
                index=False
            )

        else:

            new_data.to_csv(
                file_path,
                index=False
            )

        return jsonify({
            "status": status
        })

    except Exception as e:

        print("ERROR:", e)

        return "Error", 500


# ---------------- RUN ----------------
if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )