# app/api/inference.py
import os
import io
from pathlib import Path
from PIL import Image
import numpy as np
import tensorflow as tf

from app.utils.preprocessing import preprocess_image
from app.utils.labels import CLASS_NAMES
from app.utils.disease_info import DISEASE_INFO

# quiet TF logs
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

# robust model path (works regardless of current working directory)
HERE = Path(__file__).resolve()
PROJECT_ROOT = HERE.parents[2]
MODEL_PATH = PROJECT_ROOT / "model" / "PlantRecogModelv1.keras"

# allow override from env var if desired
env_path = os.getenv("CROP_MODEL_PATH")
if env_path:
    MODEL_PATH = Path(env_path)

def load_model(path=MODEL_PATH):
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Model file not found at: {p.resolve()}")
    model = tf.keras.models.load_model(str(p))
    return model

# load once on import
model = load_model()

def _get_info_for_label(label):
    """
    Try exact match, then case-insensitive match, then fallback to UNKNOWN.
    Returns a dict with keys 'causes' and 'suggestions'.
    """
    if label in DISEASE_INFO:
        return DISEASE_INFO[label]
    # tolerant match
    label_norm = label.strip().lower()
    for k, v in DISEASE_INFO.items():
        if k.strip().lower() == label_norm:
            return v
    # fallback
    return DISEASE_INFO.get("UNKNOWN", {"causes": [], "suggestions": []})

def predict_from_bytes(image_bytes: bytes):
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    inp = preprocess_image(img)  # numpy array shape (1,H,W,C)
    preds = model.predict(inp)[0]

    # If outputs are logits, apply softmax
    if not np.isclose(preds.sum(), 1.0):
        preds = tf.nn.softmax(preds).numpy()

    idx = int(np.argmax(preds))
    confidence = float(preds[idx])
    label = CLASS_NAMES[idx] if idx < len(CLASS_NAMES) else str(idx)

    info = _get_info_for_label(label)

    # Defensive: ensure keys exist and are lists
    causes = info.get("causes") or []
    suggestions = info.get("suggestions") or []

    # Debug print (server console)
    print(f"[DEBUG] label={label}, confidence={confidence}, causes_len={len(causes)}, suggestions_len={len(suggestions)}")

    return {
        "label": label,
        "confidence": round(confidence, 4),
        "causes": causes,
        "suggestions": suggestions,
        # include matched info for debugging (optional)
        "_matched_info": info
    }
