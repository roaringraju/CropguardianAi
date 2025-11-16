# app/ui/streamlit_app.py
import streamlit as st
import subprocess
import sys
import time
import requests
from pathlib import Path

st.set_page_config(page_title="CropGuardian AI — Local Demo", layout="centered")

API_HOST = "127.0.0.1"
API_PORT = 8000
API_URL = f"http://{API_HOST}:{API_PORT}/predict"
HEALTH_URL = f"http://{API_HOST}:{API_PORT}/healthz"

# track process in session state
if "uvicorn_proc" not in st.session_state:
    st.session_state["uvicorn_proc"] = None

st.title("🌱 CropGuardian AI — Local Demo")
st.write("Start the backend, then upload an image. Backend runs locally using uvicorn.")

col1, col2 = st.columns([1,1])

with col1:
    if st.session_state.uvicorn_proc is None:
        if st.button("▶️ Start Backend"):
            # start uvicorn as subprocess using current python interpreter
            cmd = [
                sys.executable, "-m", "uvicorn",
                "app.api.routes:app",
                "--host", API_HOST,
                "--port", str(API_PORT)
            ]
            # If you want auto-reload in dev, add "--reload" but note it will spawn child process.
            # cmd.append("--reload")
            st.session_state.uvicorn_proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            st.success("Starting backend... please wait a few seconds.")
            # small wait then check health
            time.sleep(1)
    else:
        st.info("Backend appears to be running. PID: " + str(st.session_state.uvicorn_proc.pid))

with col2:
    if st.session_state.uvicorn_proc is not None:
        if st.button("⏹ Stop Backend"):
            proc = st.session_state.uvicorn_proc
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except Exception:
                proc.kill()
            st.session_state.uvicorn_proc = None
            st.warning("Backend stopped.")

st.markdown("---")

# check backend health
backend_up = False
try:
    res = requests.get(HEALTH_URL, timeout=1.0)
    if res.status_code == 200:
        backend_up = True
except Exception:
    backend_up = False

if backend_up:
    st.success(f"Backend reachable at `{API_HOST}:{API_PORT}`")
else:
    st.info("Backend not reachable. Click **Start Backend** to launch it.")

st.header("Upload leaf image for prediction")

uploaded = st.file_uploader("Choose an image...", type=["jpg","jpeg","png"])

if uploaded:
    st.image(uploaded, caption="Uploaded image", use_column_width=True)
    st.write("")

    if backend_up:
        if st.button("Predict"):
            files = {"file": (uploaded.name, uploaded.getvalue(), uploaded.type)}
            with st.spinner("Contacting backend..."):
                try:
                    r = requests.post(API_URL, files=files, timeout=30)
                    if r.status_code == 200:
                        res = r.json()
                        st.success(f"Prediction: **{res.get('label','-')}**")
                        st.info(f"Confidence: {res.get('confidence','-')}")
                    else:
                        st.error(f"Backend error: {r.status_code} {r.text}")
                except Exception as e:
                    st.error(f"Request failed: {e}")
    else:
        st.warning("Start the backend first (click **Start Backend** above).")

st.markdown("---")
st.caption("When you finish, click Stop Backend to free the port.")
