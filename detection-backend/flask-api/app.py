# import os
# import cv2
# import numpy as np
# import tensorflow as tf
# from flask import Flask, request, jsonify
# from flask_cors import CORS
# from threading import Lock..

# # --- Initialize Flask ---
# app = Flask(__name__)
# CORS(app, resources={r"/predict": {"origins": "http://localhost:5174"}})

# # --- Model Path ---
# MODEL_PATH = os.path.join(os.path.dirname(__file__), 'models', 'waste_classifier_v2.h5')

# # --- Load Model Once ---
# if not os.path.exists(MODEL_PATH):
#     raise FileNotFoundError(f"Model file not found at {MODEL_PATH}")

# model = tf.keras.models.load_model(MODEL_PATH)
# labels = {0: "Non-Recyclable", 1: "Organic", 2: "Recyclable"}

# # --- Thread lock for TensorFlow ---
# model_lock = Lock()

# # --- Preprocess Image ---
# def preprocess_image(image):
#     img = cv2.resize(image, (224, 224))
#     img = img.astype("float32") / 255.0
#     img = np.expand_dims(img, axis=0)
#     return img

# # --- NEW: Home Route ---
# @app.route('/')
# def home():
#     """A simple route to confirm the API is running."""
#     return jsonify({
#         'status': 'online',
#         'message': 'Waste Classifier API is running.'
#     })

# # --- Prediction Endpoint ---
# @app.route('/predict', methods=['POST'])
# def predict():
#     if 'file' not in request.files:
#         return jsonify({'error': 'No file provided'}), 400

#     file = request.files['file']
#     try:
#         # Convert uploaded file to OpenCV image
#         filestr = file.read()
#         npimg = np.frombuffer(filestr, np.uint8)
#         img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
#         if img is None:
#             return jsonify({'error': 'Invalid image data'}), 400

#         # Preprocess
#         processed_img = preprocess_image(img)

#         # Thread-safe prediction
#         with model_lock:
#             preds = model.predict(processed_img, verbose=0)

#         class_id = int(np.argmax(preds[0]))
#         label = labels.get(class_id, "Unknown")
#         confidence = float(preds[0][class_id])

#         return jsonify({
#             'prediction': label,
#             'confidence': f"{confidence:.2f}"
#         })

#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

# # --- Run Flask App ---
# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5000, debug=True)



# import os
# import cv2
# import numpy as np
# from flask import Flask, request, jsonify
# from flask_cors import CORS
# from threading import Lock
# from ultralytics import YOLO

# # --- Initialize Flask ---
# app = Flask(__name__)
# CORS(app, resources={r"/predict": {"origins": "http://localhost:5173"}})

# # --- Model Path ---
# MODEL_PATH = os.path.join(os.path.dirname(__file__), 'models', 'best.pt')

# # --- Load YOLO Model Once ---
# if not os.path.exists(MODEL_PATH):
#     raise FileNotFoundError(f"Model file not found at {MODEL_PATH}")

# model = YOLO(MODEL_PATH)

# # --- Thread lock for YOLO ---
# model_lock = Lock()

# # --- Home Route ---
# @app.route('/')
# def home():
#     return jsonify({
#         'status': 'online',
#         'message': 'Waste Classifier API (YOLOv8) is running.'
#     })

# # --- Prediction Endpoint ---
# @app.route('/predict', methods=['POST'])
# def predict():
#     if 'file' not in request.files:
#         return jsonify({'error': 'No file provided'}), 400

#     file = request.files['file']
#     try:
#         # Convert uploaded file to OpenCV image
#         filestr = file.read()
#         npimg = np.frombuffer(filestr, np.uint8)
#         img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
#         if img is None:
#             return jsonify({'error': 'Invalid image data'}), 400

#         # Thread-safe YOLO prediction
#         with model_lock:
#             results = model.predict(img, verbose=False)

#         # Extract classification info
#         if hasattr(results[0], 'probs'):  # For classification model
#             probs = results[0].probs
#             class_id = int(probs.top1)
#             label = results[0].names[class_id]
#             confidence = float(probs.top1conf)
#         else:
#             return jsonify({'error': 'Model is not a classification model'}), 500

#         return jsonify({
#             'prediction': label,
#             'confidence': f"{confidence:.2f}"
#         })

#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

# # --- Run Flask App ---
# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5000, debug=True)

import os
import cv2
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS
from threading import Lock
from ultralytics import YOLO

# --- Initialize Flask ---
app = Flask(__name__)
# It's good practice to be specific with CORS in production, but for development this is fine.
CORS(app, resources={r"/predict": {"origins": "*"}})

# --- Model Path ---
# Assuming 'models/best.pt' is in the same directory as this script.
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'models', 'best.pt')

# --- Load YOLO Model Once ---
if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(f"Model file not found. Please place 'best.pt' in a 'models' folder next to this script.")

try:
    model = YOLO(MODEL_PATH)
except Exception as e:
    raise RuntimeError(f"Error loading YOLO model: {e}")


# --- Thread lock for YOLO ---
model_lock = Lock()

# --- Home Route ---
@app.route('/')
def home():
    """Provides a simple status check for the API."""
    return jsonify({
        'status': 'online',
        'message': 'Waste Classifier API (YOLOv8) is running.'
    })

# --- Prediction Endpoint ---
@app.route('/predict', methods=['POST'])
def predict():
    """Handles image uploads and returns a waste classification."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected for uploading'}), 400

    try:
        # Read the file stream into a numpy array
        filestr = file.read()
        npimg = np.frombuffer(filestr, np.uint8)
        
        # Decode the numpy array into an image
        img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
        if img is None:
            return jsonify({'error': 'Could not decode image. The file may be corrupt or in an unsupported format.'}), 400

        # Perform a thread-safe YOLO prediction
        with model_lock:
            results = model.predict(img, verbose=False)

        # Ensure the model output is for classification
        if not hasattr(results[0], 'probs'):
            return jsonify({'error': 'The loaded model does not appear to be a classification model.'}), 500

        # Extract classification info from the first result
        probs = results[0].probs
        class_id = int(probs.top1)
        label = results[0].names[class_id]
        confidence = float(probs.top1conf)

        return jsonify({
            'prediction': label,
            'confidence': f"{confidence:.2f}"
        })

    except Exception as e:
        # Log the exception for debugging purposes
        app.logger.error(f"An error occurred during prediction: {e}")
        return jsonify({'error': 'An internal server error occurred.'}), 500

# --- Run Flask App ---
if __name__ == '__main__':
    # Use debug=False in a production environment
    app.run(host='0.0.0.0', port=5000, debug=True)
