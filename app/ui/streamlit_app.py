# streamlit_app.py
import streamlit as st
import subprocess
import sys
import time
import requests
from pathlib import Path
import io

st.set_page_config(page_title="CropGuardianAI", layout="centered")

API_HOST = "127.0.0.1"
API_PORT = 8000
API_URL = f"http://{API_HOST}:{API_PORT}/predict"
HEALTH_URL = f"http://{API_HOST}:{API_PORT}/healthz"

LOG_DIR = Path.cwd() / "logs"
LOG_DIR.mkdir(exist_ok=True)

# --- minimal but themed CSS (keeps the palette, reduces verbosity) ---
st.markdown(
    """
    <style>
    :root{--accent:#14a085;--accent-dark:#0d7377;--muted:#666;--tile:#f8f9fa}
    .main-title{font-size:2.6rem;font-weight:700;color:var(--accent-dark);text-align:center;margin:1.2rem 0}
    .subtitle{font-size:1.1rem;color:var(--accent);text-align:center;background:#d4f1f4;padding:1rem;border-radius:8px;margin-bottom:1.5rem}
    .section-header{font-size:1.25rem;font-weight:600;color:var(--accent-dark);border-left:4px solid var(--accent);padding-left:12px;margin-top:1.25rem}
    .result-card,.info-tile{background:var(--tile);padding:1rem;border-radius:8px;margin:0.8rem 0;border-left:4px solid var(--accent)}
    .disease-label{font-size:1.1rem;color:var(--accent-dark);font-weight:600}
    .confidence{font-size:0.95rem;color:var(--muted)}
    .stButton>button{background:var(--accent);color:#fff;font-weight:600;border-radius:8px;padding:0.6rem 1rem}
    #MainMenu, footer{visibility:hidden}
    </style>
    """,
    unsafe_allow_html=True,
)

# --- session state defaults ---
for k in ("uvicorn_proc", "uvicorn_log", "prediction_result"):
    st.session_state.setdefault(k, None)

def start_backend():
    logfile = LOG_DIR / f"uvicorn_{int(time.time())}.log"
    fh = open(logfile, "ab")
    cmd = [
        sys.executable, "-m", "uvicorn",
        "app.api.routes:app",
        "--host", API_HOST, "--port", str(API_PORT)
    ]
    proc = subprocess.Popen(cmd, stdout=fh, stderr=subprocess.STDOUT)
    st.session_state.uvicorn_proc = proc
    st.session_state.uvicorn_log = str(logfile)
    return proc, logfile, fh

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

def wait_for_backend(timeout=30, delay=1.0):
    for _ in range(timeout):
        try:
            r = requests.get(HEALTH_URL, timeout=1.0)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(delay)
    return False

def tail_log(path, max_bytes=4000):
    p = Path(path)
    if not p.exists():
        return ""
    try:
        with p.open("rb") as fh:
            fh.seek(0, io.SEEK_END)
            size = fh.tell()
            tail_size = min(max_bytes, size)
            fh.seek(size - tail_size)
            return fh.read().decode(errors="ignore")[-max_bytes:]
    except Exception:
        return "Could not read log file."

def render_tiles(title, items):
    if not items:
        return
    st.markdown(f'<div class="section-header">{title}</div>', unsafe_allow_html=True)
    for it in items:
        st.markdown(f'<div class="info-tile">{it}</div>', unsafe_allow_html=True)

# --- header ---
st.markdown('<div class="main-title">🌱 CropGuardianAI</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Upload a leaf image for instant disease diagnosis.</div>', unsafe_allow_html=True)

# --- sidebar backend controls ---
with st.sidebar:
    st.header("⚙️ Backend Control")
    st.caption("Advanced Settings")
    col1, col2 = st.columns(2)

    backend_running = False
    # quick health probe
    try:
        r = requests.get(HEALTH_URL, timeout=0.8)
        backend_running = (r.status_code == 200)
    except Exception:
        backend_running = False

    with col1:
        if not backend_running and st.session_state.uvicorn_proc is None:
            if st.button("▶️ Start Backend"):
                proc, logp, fh = start_backend()
                with st.spinner("Starting backend..."):
                    if wait_for_backend():
                        st.success(f"✅ Backend running (PID {proc.pid})")
                    else:
                        st.error("❌ Backend did not start. Check logs below.")
        else:
            st.info(f"✅ Backend running (PID: {st.session_state.uvicorn_proc.pid if st.session_state.uvicorn_proc else 'unknown'})")

    with col2:
        if (backend_running or st.session_state.uvicorn_proc) and st.button("⏹ Stop Backend"):
            stop_backend()
            st.warning("Backend stopped.")

    if st.session_state.uvicorn_log:
        st.markdown("---")
        st.subheader("📋 Backend Logs")
        st.code(tail_log(st.session_state.uvicorn_log), language="text")

# --- auto-start backend if not up ---
# Only try auto-start when there's no tracked uvicorn process and the health probe failed.
try:
    r = requests.get(HEALTH_URL, timeout=0.8)
    backend_up = (r.status_code == 200)
except Exception:
    backend_up = False

if not backend_up and st.session_state.uvicorn_proc is None:
    with st.spinner("Auto-starting backend..."):
        proc, logp, fh = start_backend()
        if wait_for_backend():
            st.success(f"✅ Backend auto-started (PID {proc.pid})")
        else:
            st.error("❌ Auto-start failed. Check logs in the sidebar.")

# --- file upload and analyze UI ---
st.markdown('<p style="font-size:1.05rem;color:#0d7377;font-weight:600;margin-top:0.8rem">Select an image of a leaf</p>', unsafe_allow_html=True)
uploaded = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"], help="Drag & drop • Limit 200MB", label_visibility="collapsed")

if uploaded:
    c1, c2 = st.columns([1, 1])
    with c1:
        st.image(uploaded, use_container_width=True)
        st.markdown('<p style="text-align:left;color:#666;margin-top:0.4rem">Uploaded Leaf for Diagnosis</p>', unsafe_allow_html=True)

    # re-check backend before analyze
    try:
        r = requests.get(HEALTH_URL, timeout=0.8)
        backend_up = (r.status_code == 200)
    except Exception:
        backend_up = False

    if backend_up:
        if st.button("Analyze Disease"):
            files = {"file": (uploaded.name, uploaded.getvalue(), uploaded.type)}
            with st.spinner("Analyzing..."):
                try:
                    r = requests.post(API_URL, files=files, timeout=60)
                    if r.status_code == 200:
                        st.session_state.prediction_result = r.json()
                    else:
                        st.error(f"Backend error: {r.status_code} {r.text}")
                except Exception as e:
                    st.error(f"Request failed: {e}")
    else:
        st.warning("⚠️ Backend is not running. Start it from the Backend Control section.")

# --- display prediction result ---
res = st.session_state.prediction_result
if res:
    st.markdown('<div class="section-header">Diagnosis Result</div>', unsafe_allow_html=True)
    label = res.get("label", "-")
    confidence = res.get("confidence", "-")
    st.markdown(
        f"""
        <div class="result-card">
            <p class="disease-label">Predicted Disease: {label}</p>
            <p class="confidence">Confidence: {confidence}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if "healthy" in label.lower():
        render_tiles("Maintenance Tips", res.get("suggestions", []))
    else:
        render_tiles("Causes", res.get("causes", []))
        render_tiles("Treatment Suggestions", res.get("suggestions", []))

st.markdown("---")
st.caption("💡 Tip: Log files are stored in the /logs folder for troubleshooting.")
