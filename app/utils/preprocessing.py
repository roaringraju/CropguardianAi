import tensorflow as tf
import numpy as np
from tensorflow.keras.applications.efficientnet import preprocess_input

IMG_SIZE = (224, 224)

def preprocess_image(image):
    image = image.resize(IMG_SIZE)
    image = tf.keras.preprocessing.image.img_to_array(image)
    image = np.expand_dims(image, axis=0)
    image = preprocess_input(image)   # ✅ EfficientNet preprocessing
    return image

print("Preprocessing module loaded.")