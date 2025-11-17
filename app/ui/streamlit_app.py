# app/ui/streamlit_app.py
import streamlit as st
import subprocess
import sys
import time
import requests
from pathlib import Path
import io

st.set_page_config(
    page_title="CropGuardianAI", 
    layout="centered",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

API_HOST = "127.0.0.1"
API_PORT = 8000
API_URL = f"http://{API_HOST}:{API_PORT}/predict"
HEALTH_URL = f"http://{API_HOST}:{API_PORT}/healthz"

LOG_DIR = Path.cwd() / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Custom CSS for modern UI
st.markdown("""
<style>
    /* Main title styling */
    .main-title {
        font-size: 3rem;
        font-weight: 700;
        color: #0d7377;
        text-align: center;
        margin-bottom: 3rem;
        margin-top: 2rem;
    }
    
    /* Subtitle styling */
    .subtitle {
        font-size: 1.5rem;
        color: #14a085;
        text-align: center;
        background-color: #d4f1f4;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 3rem;
    }
    
    /* Section headers */
    .section-header {
        font-size: 1.8rem;
        font-weight: 600;
        color: #0d7377;
        border-left: 5px solid #14a085;
        padding-left: 15px;
        margin-top: 2rem;
        margin-bottom: 1.5rem;
    }
    
    /* Result card styling */
    .result-card {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #14a085;
    }
    
    .disease-label {
        font-size: 1.5rem;
        color: #0d7377;
        font-weight: 600;
    }
    
    .confidence {
        font-size: 1rem;
        color: #666;
    }
    
    /* List items styling - consistent tiles */
    .info-tile {
        background-color: #f8f9fa;
        padding: 1.2rem 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #14a085;
        font-size: 1rem;
        color: #333;
    }
    
    /* Button styling */
    .stButton>button {
        background-color: #14a085;
        color: white;
        font-weight: 600;
        border-radius: 8px;
        padding: 0.75rem 2rem;
        width: 100%;
        border: none;
        font-size: 1.1rem;
    }
    
    .stButton>button:hover {
        background-color: #0d7377;
    }
    
    /* Upload area styling */
    .uploadedFile {
        border: 2px dashed #14a085;
        border-radius: 10px;
        padding: 1rem;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: visible;}
    
    /* Image container alignment */
    .image-container {
        display: flex;
        justify-content: flex-start;
        margin: 1rem 0;
    }
    
    .image-wrapper {
        max-width: 50%;
    }
    
    /* Centered image caption */
    .image-caption {
        text-align: center;
        color: #666;
        font-size: 1rem;
        margin-top: 0.5rem;
    }
</style>
<script>
    // Move sidebar toggle to right side using JavaScript
    const moveToggle = () => {
        const toggle = document.querySelector('[data-testid="collapsedControl"]');
        if (toggle) {
            toggle.style.left = 'auto';
            toggle.style.right = '5rem';
            toggle.style.position = 'fixed';
        }
    };
    
    // Run on load and observe for changes
    moveToggle();
    const observer = new MutationObserver(moveToggle);
    observer.observe(document.body, { childList: true, subtree: true });
</script>
""", unsafe_allow_html=True)

# Session state keys
if "uvicorn_proc" not in st.session_state:
    st.session_state.uvicorn_proc = None
if "uvicorn_log" not in st.session_state:
    st.session_state.uvicorn_log = None
if "prediction_result" not in st.session_state:
    st.session_state.prediction_result = None

def start_backend():
    logfile = LOG_DIR / f"uvicorn_{int(time.time())}.log"
    log_fh = open(logfile, "ab")
    cmd = [
        sys.executable, "-m", "uvicorn",
        "app.api.routes:app",
        "--host", API_HOST,
        "--port", str(API_PORT)
    ]
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

# Header with logo-like styling
st.markdown('<div class="main-title">🌱 CropGuardianAI</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Upload a leaf image for instant disease diagnosis.</div>', unsafe_allow_html=True)

# Backend control in sidebar
with st.sidebar:
    st.header("⚙️ Backend Control")
    st.caption("Advanced Settings")
    st.markdown("---")
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.session_state.uvicorn_proc is None:
            if st.button("▶️ Start Backend"):
                proc, logfile, log_fh = start_backend()
                with st.spinner("Starting backend..."):
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
                        st.success(f"✅ Backend is running (PID {proc.pid})")
                    else:
                        st.error("❌ Backend did not start. Check logs below.")
        else:
            st.info(f"✅ Backend running (PID: {st.session_state.uvicorn_proc.pid})")
    
    with col2:
        if st.session_state.uvicorn_proc is not None:
            if st.button("⏹ Stop Backend"):
                stop_backend()
                st.warning("Backend stopped.")
    
    # Show logs
    if st.session_state.uvicorn_log:
        st.markdown("---")
        st.subheader("📋 Backend Logs")
        log_path = Path(st.session_state.uvicorn_log)
        if log_path.exists():
            try:
                with log_path.open("rb") as fh:
                    fh.seek(0, io.SEEK_END)
                    size = fh.tell()
                    tail_size = min(8192, size)
                    fh.seek(size - tail_size)
                    tail = fh.read().decode(errors="ignore")
                st.code(tail[-4000:], language="text")
            except Exception as e:
                st.write("Could not read log file:", e)

# Check backend health
backend_up = False
try:
    res = requests.get(HEALTH_URL, timeout=1.0)
    if res.status_code == 200:
        backend_up = True
except Exception:
    backend_up = False

# Auto-start backend if not running
if not backend_up and st.session_state.uvicorn_proc is None:
    with st.spinner("Auto-starting backend..."):
        proc, logfile, log_fh = start_backend()
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

# Main upload section
st.markdown('<p style="font-size: 1.2rem; font-weight: 600; color: #0d7377; margin-bottom: 1rem; margin-top: 1rem;">Select an image of a leaf</p>', unsafe_allow_html=True)

uploaded = st.file_uploader(
    "Choose an image...", 
    type=["jpg", "jpeg", "png"],
    help="Drag and drop file here • Limit 200MB per file • PNG, JPG, JPEG",
    label_visibility="collapsed"
)

if uploaded:
    # Create columns for left-aligned image at 50% width
    col_img, col_space = st.columns([1, 1])
    with col_img:
        st.image(uploaded, caption="", use_container_width=True)
        st.markdown('<p style="text-align: left; color: #666; font-size: 1rem; margin-top: 0.5rem;">Uploaded Leaf for Diagnosis</p>', unsafe_allow_html=True)
    st.write("")
    
    if backend_up:
        if st.button("Analyze Disease", type="primary"):
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
        st.warning("⚠️ Backend is not running. Please start it from the Backend Control section above.")

# Display results
if st.session_state.prediction_result:
    res = st.session_state.prediction_result
    
    st.markdown('<div class="section-header">Diagnosis Result</div>', unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="result-card">
        <p class="disease-label">Predicted Disease: {res.get('label', '-')}</p>
        <p class="confidence">Confidence: {res.get('confidence', '-')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Causes section
    causes = res.get("causes", [])
    if causes:
        st.markdown('<div class="section-header">Causes</div>', unsafe_allow_html=True)
        for cause in causes:
            st.markdown(f"""
            <div class="info-tile">
                {cause}
            </div>
            """, unsafe_allow_html=True)
    
    # Treatment suggestions section
    suggestions = res.get("suggestions", [])
    if suggestions:
        st.markdown('<div class="section-header">Treatment Suggestions</div>', unsafe_allow_html=True)
        for suggestion in suggestions:
            st.markdown(f"""
            <div class="info-tile">
                {suggestion}
            </div>
            """, unsafe_allow_html=True)

st.markdown("---")
st.caption("💡 Tip: Log files are stored in the /logs folder for troubleshooting.")