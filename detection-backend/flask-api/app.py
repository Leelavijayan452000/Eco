import os
import cv2
import numpy as np
import sqlite3
from flask import Flask, request, jsonify
from flask_cors import CORS
from threading import Lock
from ultralytics import YOLO
from datetime import datetime

# --- Initialize Flask ---
app = Flask(__name__)
CORS(app, resources={r"/predict": {"origins": "*"}})

# --- Database Setup ---
DB_PATH = "predictions.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            label TEXT,
            confidence REAL,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# --- Model Path ---
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'models', 'best.pt')

if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError("Model file not found. Place 'best.pt' in a 'models' folder.")

try:
    model = YOLO(MODEL_PATH)
except Exception as e:
    raise RuntimeError(f"Error loading YOLO model: {e}")

# --- Thread lock for YOLO ---
model_lock = Lock()

# --- Define Your Two Classes ---
CLASS_NAMES = ["hazardous", "organic"]

# --- Home Route ---
@app.route('/')
def home():
    return jsonify({
        'status': 'online',
        'message': '2-Class Waste Classifier API (hazardous vs organic) with DB storage.'
    })

# --- Prediction Endpoint ---
@app.route('/predict', methods=['POST'])
def predict():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected for uploading'}), 400

    try:
        # Read the file stream into a numpy array
        filestr = file.read()
        npimg = np.frombuffer(filestr, np.uint8)
        img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

        if img is None:
            return jsonify({'error': 'Could not decode image.'}), 400

        # Perform a thread-safe YOLO prediction
        with model_lock:
            results = model.predict(img, verbose=False)

        # Ensure the model output is classification
        if not hasattr(results[0], 'probs'):
            return jsonify({'error': 'The loaded model is not a classification model.'}), 500

        # Extract classification info
        probs = results[0].probs
        class_id = int(probs.top1)

        # Map to hazardous/organic
        if class_id >= len(CLASS_NAMES):
            return jsonify({'error': f'Invalid class id {class_id} returned by model'}), 500

        label = CLASS_NAMES[class_id]
        confidence = float(probs.top1conf)

        # --- Save to Database ---
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO predictions (filename, label, confidence, timestamp)
            VALUES (?, ?, ?, ?)
        """, (file.filename, label, confidence, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()

        return jsonify({
            'prediction': label,
            'confidence': f"{confidence:.2f}",
            'filename': file.filename
        })

    except Exception as e:
        app.logger.error(f"Error during prediction: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# --- Run Flask App ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
