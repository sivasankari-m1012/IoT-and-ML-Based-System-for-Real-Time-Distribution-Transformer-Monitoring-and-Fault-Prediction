import pandas as pd
from sklearn.ensemble import IsolationForest
from flask import Flask, render_template, request
import joblib

app = Flask(__name__)

# ===== TRAIN MODEL =====
file_path = r"C:\Users\ganesan\Music\PROJECT\training_data.xlsx"

df = pd.read_excel(file_path)
X = df[["Voltage", "Current", "Temperature", "Power"]]

model = IsolationForest(contamination=0.1, random_state=42)
model.fit(X)
joblib.dump(model, "iforest_model.pkl")

model = joblib.load("iforest_model.pkl")

@app.route("/", methods=["GET", "POST"])
def home():
    status = ""
    reason = ""

    if request.method == "POST":
        v = float(request.form["voltage"])
        c = float(request.form["current"])
        t = float(request.form["temperature"])
        p = float(request.form["power"])

        input_data = pd.DataFrame(
            [[v, c, t, p]],
            columns=["Voltage", "Current", "Temperature", "Power"]
        )

        result = model.predict(input_data)

        # ===== REASON LOGIC BASED ON YOUR DATA =====
        if t > 30:
            status = "FAULT"
            reason = "Over Heat"

        elif c > 6:
            status = "FAULT"
            reason = "Over Current"

        elif v > 15:
            status = "FAULT"
            reason = "Over Voltage"

        elif p > 100:
            status = "FAULT"
            reason = "Over Power"

        elif result[0] == -1:
            status = "FAULT"
            reason = "Abnormal Pattern (ML Detected)"

        else:
            status = "NORMAL"
            reason = "System Operating Normally"

    return render_template("index.html", status=status, reason=reason)

if __name__ == "__main__":
    app.run(debug=True)