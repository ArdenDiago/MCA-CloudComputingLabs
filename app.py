import streamlit as st
import requests

API = "http://localhost:8000"

REGION_LABELS = {
    "us-east-1": "us-east-1  (N. Virginia) [AWS Academy]",
    "us-east-2": "us-east-2  (Ohio)",
    "us-west-1": "us-west-1  (N. California)",
    "us-west-2": "us-west-2  (Oregon)",
    "ap-south-1": "ap-south-1  (Mumbai)",
    "ap-southeast-1": "ap-southeast-1  (Singapore)",
    "ap-southeast-2": "ap-southeast-2  (Sydney)",
    "ap-northeast-1": "ap-northeast-1  (Tokyo)",
    "eu-west-1": "eu-west-1  (Ireland)",
    "eu-central-1": "eu-central-1  (Frankfurt)",
}

ACL_OPTIONS = {
    "private": "Private — owner access only",
    "public-read": "Public Read — anyone can read",
    "authenticated-read": "Authenticated Read — any AWS account",
}


def parse_error(resp):
    try:
        return resp.json().get("detail", resp.text)
    except Exception:
        return resp.text or f"HTTP {resp.status_code} — empty response from backend"


def load_buckets():
    try:
        resp = requests.get(f"{API}/list-buckets", timeout=5)
        if resp.ok:
            st.session_state["buckets"] = resp.json()["buckets"]
        else:
            st.session_state["buckets"] = []
    except Exception:
        st.session_state["buckets"] = []


# Auto-load bucket list on first run
if "buckets" not in st.session_state:
    load_buckets()

# ── Page header ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="S3 Manager", page_icon="🪣", layout="wide")
st.title("Amazon S3 Manager")
st.caption("Create buckets, upload files, and manage object access levels")

# ── Bucket refresh bar ────────────────────────────────────────────────────────
col_btn, col_status = st.columns([1, 5])
with col_btn:
    if st.button("Refresh Buckets", use_container_width=True):
        load_buckets()
        st.rerun()
with col_status:
    buckets: list = st.session_state.get("buckets", [])
    if buckets:
        st.success(f"{len(buckets)} bucket(s) found: {', '.join(buckets)}")
    else:
        st.warning("No buckets found — create one below or check your credentials.")

st.divider()

tab1, tab2, tab3, tab4 = st.tabs(["Create Bucket", "Bucket Files", "Change Access Level", "Delete Bucket"])
