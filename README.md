# 🌱 CropGuardianAI — Plant Disease Detection Using EfficientNet-B3

CropGuardianAI is a deep-learning–powered plant disease detection system built using **TensorFlow**, **EfficientNet-B3**, **FastAPI**, and **Streamlit**.  
Users can upload a leaf image and instantly get predictions along with probable causes and treatment suggestions.

---

## 🚀 Features

- 🧠 **EfficientNet-B3 Transfer Learning**  
  Fine-tuned on a custom dataset derived from **PlantVillage** and **PlantDoc**, containing **38 plant disease classes**.

- 🎯 **High Accuracy**  
  Achieved **~96% accuracy** on validation and test sets after carefully freezing/unfreezing layers (excluding `BatchNormalization` layers).

- ⚡ **FastAPI Backend**  
  High-performance REST API serving predictions.

- 🖥️ **Streamlit Frontend**  
  Clean UI that allows users to upload leaf images and view results.

- 🎨 **Custom CSS**  
  Modern themed UI with styled result cards and sections.

---

## 📁 Dataset

- Combined dataset from:
  - **PlantVillage**
  - **PlantDoc**
- Total classes: **38 plant diseases**
- Preprocessing done:
  - Train/Validation/Test split  
  - Normalization  
  - Augmentation  

> Please cite original dataset sources if using this repository.

---

## 🏗️ Project Structure

CropGuardianAI/
│── app/
│ ├── api/
│ │ ├── routes.py # FastAPI routes
│ │ └── inference.py # Model loading & prediction logic
│ ├── ui/
│ │ └── streamlit_app.py # Streamlit Web UI
│ └── utils/
│   └── labels.py
|   └── diseaseinfo.py
|   └── preprocess.py
│
│── model/
│ └── model.keras # Trained EfficientNet-B3 model
│
│── logs/
│ └── uvicorn_xxx.log # Backend logs
│
├── requirements.txt
└── README.md


---

## 🧪 Model Training Summary

- **Base Model:** EfficientNet-B3 (ImageNet pre-trained)
- **Framework:** TensorFlow / keras
- **Layers Trained:**
  - Initial 150 layers kept frozen
  - BatchNormalization layers kept frozen
  - Rest 114 layers trained
- **Metrics:**
  - Validation Accuracy: **~96%**
  - Test Accuracy: **~96%**
- **Loss Function:** Sparse Categorical Crossentropy  
- **Optimizer:** Adam  

---

## 🔧 Tech Stack

### python version
 - pyhton 3.13.7 

### Frontend
- Streamlit  
- CSS  

### Backend
- FastAPI  
- Uvicorn  

### Model
- TensorFlow  
- EfficientNet-B3

---

## 📦 Installation and Execution

Clone the repository and run : 
Note : clone in python 3.13.7

```bash
git clone https://github.com/roaringraju/CropguardianAi.git
cd CropguardianAi
pip install requirements.txt
streamlit run app/ui/streamlit_app.py
```

## 📸 UI Screenshots
<img width="1851" height="974" alt="Screenshot 2025-11-22 024155" src="https://github.com/user-attachments/assets/ad76d122-0481-4834-a6d5-4d517c732242" />
<img width="1841" height="963" alt="Screenshot 2025-11-22 024553" src="https://github.com/user-attachments/assets/d47430be-c310-45f1-a665-319429fc7ec6" />
<img width="1841" height="964" alt="Screenshot 2025-11-22 024624" src="https://github.com/user-attachments/assets/553619ba-0cf3-409f-b752-9838e90d69cd" />
<img width="1854" height="973" alt="Screenshot 2025-11-22 024645" src="https://github.com/user-attachments/assets/9bc4af28-73b2-46e9-9f26-0db8d24de16b" />



