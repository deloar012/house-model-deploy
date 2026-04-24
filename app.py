import pandas as pd
import numpy as np
import joblib
from flask import Flask, render_template, request
# import mysql.connector

app = Flask(__name__)

# Load model + columns
model, columns = joblib.load("model.pkl")

flat_models = [
    "Multi Generation", "New Generation", "Premium Apartment",
    "Premium Apartment Loft", "Premium Maisonette", "Simplified",
    "Standard", "Terrace", "Type S1", "Type S2"
]

import mysql.connector
from mysql.connector import Error

# db = None
# cursor = None

# try:
#     db = mysql.connector.connect(
#         host="localhost",
#         user="deloar",
#         password="deloar8172",
#         database="house_price_db"
#     )
#     cursor = db.cursor()
#     print("✅ DB connected successfully")

# except Error as e:
#     print("⚠️ DB connection failed:", e)
#     db = None
#     cursor = None
@app.route("/")
def home():
    return render_template("index.html", models=flat_models)


@app.route("/predict", methods=["POST"])
def predict():
    try:
        # ---------------- INPUT ----------------
        data = {
            "rooms": int(request.form["rooms"]),
            "latitude": float(request.form["latitude"]),
            "longitude": float(request.form["longitude"]),
            "storey": int(request.form["storey"]),
            "area_sqm": float(request.form["area_sqm"]),
            "lease_start": int(request.form["lease_start"]),
            "lease_rem": int(request.form["lease_rem"]),
            "core_cpi": float(request.form["core_cpi"]),
            "bala_lease_pct": float(request.form["bala_lease_pct"]),
            "flat_model": request.form["flat_model"]
        }

        # ---------------- VALIDATION ----------------
        if data["area_sqm"] > 307:
            return render_template("index.html", result="❌ Max area is 307", models=flat_models)

        if data["rooms"] > 6:
            return render_template("index.html", result="❌ Max rooms is 6", models=flat_models)

        if not (-90 <= data["latitude"] <= 90):
            return render_template("index.html", result="❌ Invalid latitude", models=flat_models)

        if not (-180 <= data["longitude"] <= 180):
            return render_template("index.html", result="❌ Invalid longitude", models=flat_models)

        # ---------------- PREPROCESS ----------------
        df = pd.DataFrame([data])
        df = pd.get_dummies(df, columns=["flat_model"])
        df = df.reindex(columns=columns, fill_value=0)

        # ---------------- PREDICT ----------------
        pred_log = model.predict(df)
        pred_price = np.expm1(pred_log)[0]

        # ---------------- SAVE TO MYSQL ----------------
        sql = """
        INSERT INTO predictions (
            rooms, latitude, longitude, storey, area_sqm,
            lease_start, lease_rem, core_cpi, bala_lease_pct,
            flat_model, predicted_price
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """

        values = (
            data["rooms"],
            data["latitude"],
            data["longitude"],
            data["storey"],
            data["area_sqm"],
            data["lease_start"],
            data["lease_rem"],
            data["core_cpi"],
            data["bala_lease_pct"],
            data["flat_model"],
            float(pred_price)
        )

        # cursor.execute(sql, values)
        # db.commit()

        return render_template(
            "index.html",
            result=f"₹ {int(pred_price)}",
            models=flat_models
        )

    except Exception as e:
        return render_template(
            "index.html",
            result=f"Error: {str(e)}",
            models=flat_models
        )
# IMPORTANT: ONLY ONE RUN BLOCK
if __name__ == "__main__":
    app.run()