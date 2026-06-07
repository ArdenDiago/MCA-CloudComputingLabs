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

# ── Tab 1: Create Bucket ──────────────────────────────────────────────────────
with tab1:
    st.header("Create S3 Bucket")

    col1, col2 = st.columns(2)
    with col1:
        bucket_name = st.text_input(
            "New Bucket Name",
            placeholder="my-unique-bucket-name",
            help="Must be globally unique, lowercase, 3-63 characters",
        )
    with col2:
        region = st.selectbox(
            "Region",
            list(REGION_LABELS.keys()),
            format_func=lambda r: REGION_LABELS[r],
        )

    allow_public = st.toggle(
        "Allow Public Objects",
        value=False,
        help="Disables S3 Block Public Access so objects can be set to public-read",
    )

    # Existing buckets panel with duplicate highlight
    existing = st.session_state.get("buckets", [])
    if existing:
        with st.expander(f"Existing Buckets ({len(existing)})", expanded=True):
            for b in existing:
                if bucket_name and b == bucket_name:
                    st.markdown(
                        f"<span style='color:red; font-weight:bold'>⚠ {b} — name already taken</span>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(f"• {b}")

    # Warn before the button if name is taken
    name_taken = bucket_name in existing if bucket_name else False

    # Color the input box red (taken) or green (available)
    if bucket_name:
        border_color = "#cc0000" if name_taken else "#00aa44"
        st.markdown(
            f"""
            <style>
            [data-testid="stTextInput"]:has(input[placeholder="my-unique-bucket-name"]) input {{
                border-color: {border_color} !important;
                box-shadow: 0 0 0 2px {border_color}55 !important;
            }}
            </style>
            """,
            unsafe_allow_html=True,
        )

    if name_taken:
        st.error(f"'{bucket_name}' already exists. Choose a different name.")

    if st.button("Create Bucket", type="primary", disabled=name_taken):
        if not bucket_name:
            st.error("Bucket name is required")
        else:
            with st.spinner("Creating bucket..."):
                try:
                    resp = requests.post(
                        f"{API}/create-bucket",
                        data={
                            "bucket_name": bucket_name,
                            "region": region,
                            "allow_public": str(allow_public).lower(),
                        },
                    )
                    if resp.ok:
                        st.success(resp.json()["message"])
                        if allow_public:
                            st.info("Public access enabled — objects can be set to public-read.")
                        load_buckets()   # refresh list after creation
                        st.rerun()
                    else:
                        st.error(parse_error(resp))
                except requests.ConnectionError:
                    st.error("Cannot reach backend — make sure `uvicorn backend:app --reload` is running")
                except Exception as e:
                    st.error(str(e))
