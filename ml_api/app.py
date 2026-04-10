from flask import Flask, request, jsonify
import joblib
import pandas as pd

app = Flask(__name__)

# Load models
failure_model = joblib.load("failure_model.pkl")
fault_model = joblib.load("fault_model.pkl")
scaler = joblib.load("scaler.pkl")
feature_columns = joblib.load("feature_columns.pkl")

@app.route("/")
def home():
    return "Predictive Maintenance API Running"

@app.route("/predict", methods=["POST"])
def predict():

    data = request.json

    try:
        # ---------------- INPUT ----------------
        base_input = {
            'Air temperature [K]': float(data["air_temp"]),
            'Process temperature [K]': float(data["process_temp"]),
            'Rotational speed [rpm]': float(data["speed"]),
            'Torque [Nm]': float(data["torque"]),
            'Tool wear [min]': float(data["tool_wear"]),
            'Type': data["type"]
        }

        input_df = pd.DataFrame([base_input])

        # ---------------- ENCODING ----------------
        input_encoded = pd.get_dummies(input_df)

        for col in feature_columns:
            if col not in input_encoded.columns:
                input_encoded[col] = 0

        input_encoded = input_encoded[feature_columns]

        # ---------------- SCALING ----------------
        input_scaled = scaler.transform(input_encoded)

        # ---------------- PREDICTION ----------------
        prediction = failure_model.predict(input_scaled)[0]

        prob = failure_model.predict_proba(input_scaled)[0]
        confidence = float(max(prob))

        # ---------------- RESPONSE ----------------
        response = {
            "failure": int(prediction),
            "confidence": round(confidence, 3)
        }

        # ---------------- FAULT TYPE ----------------
        if prediction == 1:
            fault_prediction = fault_model.predict(input_scaled)[0]

            # OPTIONAL: Better names
            fault_map = {
                "HDF": "Heat Dissipation Failure",
                "TWF": "Tool Wear Failure",
                "PWF": "Power Failure",
                "OSF": "Overstrain Failure",
                "RNF": "Random Failure"
            }

            response["fault_type"] = fault_map.get(str(fault_prediction), str(fault_prediction))
        else:
            response["fault_type"] = "No Failure"

        return jsonify(response)

    except Exception as e:
        return jsonify({"error": str(e)})

# ---------------- RUN SERVER ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)