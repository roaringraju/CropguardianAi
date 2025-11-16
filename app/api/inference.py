import tensorflow as tf
from PIL import Image
import numpy as np
import io

from app.utils.preprocessing import preprocess_image
from app.utils.labels import CLASS_NAMES

MODEL_PATH = "model\PlantRecogModelv1.keras"

# Load TF model once
model = tf.keras.models.load_model(MODEL_PATH)

def predict_from_bytes(image_bytes):
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    
    processed = preprocess_image(img)
    preds = model.predict(processed)[0]

    idx = int(np.argmax(preds))
    confidence = float(preds[idx])

    return {
        "label": CLASS_NAMES[idx],
        "confidence": round(confidence, 4)
    }
print("Inference module loaded.")