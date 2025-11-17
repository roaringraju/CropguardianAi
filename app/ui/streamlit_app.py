# app/ui/streamlit_app.py
import streamlit as st
import subprocess
import sys
import time
import requests
from pathlib import Path
import os
import io

st.set_page_config(page_title="CropGuardian AI — Local Demo", layout="centered")

API_HOST = "127.0.0.1"
API_PORT = 8000
API_URL = f"http://{API_HOST}:{API_PORT}/predict"
HEALTH_URL = f"http://{API_HOST}:{API_PORT}/healthz"

LOG_DIR = Path.cwd() / "logs"
LOG_DIR.mkdir(exist_ok=True)

# session state keys
if "uvicorn_proc" not in st.session_state:
    st.session_state.uvicorn_proc = None
if "uvicorn_log" not in st.session_state:
    st.session_state.uvicorn_log = None

st.title("🌱 CropGuardian AI — Local Demo")
st.write("Start the backend, then upload an image. Backend runs locally using uvicorn.")

col1, col2 = st.columns([1,1])

def start_backend():
    logfile = LOG_DIR / f"uvicorn_{int(time.time())}.log"
    # Open log file in append binary mode
    log_fh = open(logfile, "ab")
    cmd = [
        sys.executable, "-m", "uvicorn",
        "app.api.routes:app",
        "--host", API_HOST,
        "--port", str(API_PORT)
    ]
    # Start uvicorn, redirect stdout/stderr to the file (avoid PIPE deadlock)
    proc = subprocess.Popen(cmd, stdout=log_fh, stderr=subprocess.STDOUT)
    st.session_state.uvicorn_proc = proc
    st.session_state.uvicorn_log = str(logfile)
    return proc, logfile, log_fh

def stop_backend():
    proc = st.session_state.uvicorn_proc
    if not proc:
        return
    try:
        proc.terminate()
        proc.wait(timeout=5)
    except Exception:
        proc.kill()
    st.session_state.uvicorn_proc = None
    st.session_state.uvicorn_log = None

with col1:
    if st.session_state.uvicorn_proc is None:
        if st.button("▶️ Start Backend"):
            proc, logfile, log_fh = start_backend()
            st.success("Backend process started. Waiting for health check...")

            # Poll health for up to 30 seconds
            backend_up = False
            timeout = 30
            for i in range(timeout):
                try:
                    r = requests.get(HEALTH_URL, timeout=1.0)
                    if r.status_code == 200:
                        backend_up = True
                        break
                except Exception:
                    pass
                time.sleep(1)

            if backend_up:
                st.success(f"Backend is healthy at `{API_HOST}:{API_PORT}` (PID {proc.pid})")
            else:
                st.error("Backend did not respond to /healthz within 30s. Check logs below.")
    else:
        st.info("Backend appears to be running. PID: " + str(st.session_state.uvicorn_proc.pid))

with col2:
    if st.session_state.uvicorn_proc is not None:
        if st.button("⏹ Stop Backend"):
            stop_backend()
            st.warning("Backend stopped.")

st.markdown("---")

# Show last lines of the uvicorn log if available
if st.session_state.uvicorn_log:
    st.subheader("Backend log (tail)")
    log_path = Path(st.session_state.uvicorn_log)
    if log_path.exists():
        try:
            with log_path.open("rb") as fh:
                # read last ~8 KB and decode (works for reasonably small logs)
                fh.seek(0, io.SEEK_END)
                size = fh.tell()
                tail_size = min(8192, size)
                fh.seek(size - tail_size)
                tail = fh.read().decode(errors="ignore")
            st.code(tail[-4000:], language="text")  # show last 4000 chars
        except Exception as e:
            st.write("Could not read log file:", e)
    else:
        st.write("No log file found yet.")
else:
    st.info("No backend log available. Start backend to create logs.")

# check backend health (quick check)
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
                    r = requests.post(API_URL, files=files, timeout=60)
                    if r.status_code == 200:
                        res = r.json()
                        st.success(f"Prediction: **{res.get('label','-')}**")
                        st.info(f"Confidence: {res.get('confidence','-')}")
                        # Show causes and solutions if present
                        causes = res.get("causes", [])
                        suggestions = res.get("suggestions", [])
                        if causes:
                            st.markdown("**Common causes:**")
                            for c in causes:
                                st.write("- " + c)
                        if suggestions:
                            st.markdown("**Suggested actions / remedies:**")
                            for s in suggestions:
                                st.write("- " + s)
                    else:
                        st.error(f"Backend error: {r.status_code} {r.text}")
                except Exception as e:
                    st.error(f"Request failed: {e}")
    else:
        st.warning("Start the backend first (click **Start Backend** above).")

st.markdown("---")
st.caption("When you finish, click Stop Backend to free the port. Log files are stored in the /logs folder.")
