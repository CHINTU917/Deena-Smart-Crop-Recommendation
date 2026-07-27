import numpy as np
import pandas as pd
import tensorflow as tf
import joblib
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# Load AI model and preprocessing
model = tf.keras.models.load_model("take2.h5", compile=False)
preprocessor = joblib.load("preprocessor.pkl")
le = joblib.load("label_encoder.pkl")

# Store latest sensor data
latest_sensors = {"n":0,"p":0,"k":0,"ph":0,"temp":0,"hum":0}

def get_month_name(month_num):
    months = ['Jan','Feb','Mar','Apr','May','Jun',
              'Jul','Aug','Sep','Oct','Nov','Dec']
    return months[max(0,min(int(round(month_num))-1,11))]

@app.route('/')
def home():
    return render_template('index.html')



# 1️ Python bridge sends sensors

@app.route('/api/sensors', methods=['POST'])
def update_sensors():

    global latest_sensors

    latest_sensors = request.json

    return jsonify({"status":"received"})



# 2️ Dashboard requests prediction

@app.route('/api/predict', methods=['POST'])
def predict():

    global latest_sensors

    user_data = request.json

    soil = user_data.get('soil')
    season = user_data.get('season')
    water_source = user_data.get('water_source')

    # Convert month to number
    sown_month = user_data.get('sown_month')
    month_num = 6
    if sown_month:
        month_num = int(sown_month.split("-")[1])

    # Prepare model input
    input_df = pd.DataFrame([{
        'SOIL': soil,
        'SEASON': season,
        'SOWN': month_num,
        'WATER_SOURCE': water_source,
        'SOIL_PH': float(latest_sensors['ph']),
        'SOIL_PH_HIGH': 8.0,
        'TEMP': float(latest_sensors['temp']),
        'MAX_TEMP': 40.0,
        'RELATIVE_HUMIDITY': float(latest_sensors['hum']),
        'RELATIVE_HUMIDITY_MAX': 95.0,
        'N': float(latest_sensors['n']),
        'N_MAX': 100.0,
        'P': float(latest_sensors['p']),
        'P_MAX': 100.0,
        'K': float(latest_sensors['k']),
        'K_MAX': 100.0,
        'N-Ratio': float(latest_sensors['n'])/100,
        'P-Ratio': float(latest_sensors['p'])/100,
        'K-Ratio': float(latest_sensors['k'])/100
    }])

    processed = preprocessor.transform(input_df)
    processed = processed.astype('float32')

    preds = model.predict(processed)

    crop = le.inverse_transform([np.argmax(preds[0])])[0]
    water = round(float(preds[1][0][0]),2)
    harvest = get_month_name(preds[1][0][1])
    duration = int(preds[1][0][2])

    return jsonify({
        "crop": crop,
        "water": water,
        "harvest": harvest,
        "duration": duration,
        "sensors": latest_sensors
    })


if __name__ == "__main__":
    app.run(debug=True,host='0.0.0.0')