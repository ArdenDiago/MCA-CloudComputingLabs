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

    # Show result from previous create attempt (set before st.rerun())
    if "create_bucket_result" in st.session_state:
        result = st.session_state.pop("create_bucket_result")
        if result["ok"]:
            st.success(result["message"])
            if result.get("public"):
                st.info("Public access enabled — objects can be set to public-read.")
        else:
            st.error(result["message"])

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
                        st.session_state["create_bucket_result"] = {
                            "ok": True,
                            "message": resp.json()["message"],
                            "public": allow_public,
                        }
                        load_buckets()
                        st.rerun()
                    else:
                        st.error(parse_error(resp))
                except requests.ConnectionError:
                    st.error("Cannot reach backend — make sure `uvicorn backend:app --reload` is running")
                except Exception as e:
                    st.error(str(e))

# ── Tab 2: Bucket Files ───────────────────────────────────────────────────────
with tab2:
    st.header("Bucket Files")

    buckets = st.session_state.get("buckets", [])

    if not buckets:
        st.warning("No buckets found — create one first or click **Refresh Buckets** at the top.")
    else:
        bf_bucket = st.selectbox("Select Bucket", buckets, key="bf_bucket_select")

        # Clear file list whenever the selected bucket changes
        if st.session_state.get("bf_bucket_loaded") != bf_bucket:
            st.session_state.pop("bf_files", None)
            st.session_state.pop("bf_bucket_loaded", None)

        col_load, _ = st.columns([1, 5])
        with col_load:
            if st.button("Load Files", use_container_width=True):
                with st.spinner("Loading files..."):
                    try:
                        resp = requests.get(f"{API}/list-objects/{bf_bucket}", timeout=10)
                        if resp.ok:
                            st.session_state["bf_files"] = resp.json()["objects"]
                            st.session_state["bf_bucket_loaded"] = bf_bucket
                        else:
                            st.error(parse_error(resp))
                    except requests.ConnectionError:
                        st.error("Cannot reach backend — make sure `uvicorn backend:app --reload` is running")
                    except Exception as e:
                        st.error(str(e))

        # ── File list ──────────────────────────────────────────────────────────
        if "bf_files" in st.session_state:
            files = st.session_state["bf_files"]

            if not files:
                st.info(f"No files in **{bf_bucket}** — upload some below.")
            else:
                st.markdown(f"**{len(files)} file(s) in `{bf_bucket}`**")

                for i, fname in enumerate(files):
                    with st.expander(fname):
                        btn_view, btn_del = st.columns(2)

                        with btn_view:
                            if st.button("View / Get URL", key=f"bf_view_{i}", use_container_width=True):
                                try:
                                    resp = requests.get(
                                        f"{API}/get-object-url/{bf_bucket}/{fname}", timeout=10
                                    )
                                    if resp.ok:
                                        url = resp.json()["url"]
                                        st.markdown(f"[Open file]({url})")
                                        st.code(url, language=None)
                                    else:
                                        st.error(parse_error(resp))
                                except requests.ConnectionError:
                                    st.error("Cannot reach backend")
                                except Exception as e:
                                    st.error(str(e))

                        with btn_del:
                            if st.button("Delete", key=f"bf_del_{i}", type="primary", use_container_width=True):
                                try:
                                    resp = requests.delete(
                                        f"{API}/delete-object/{bf_bucket}/{fname}", timeout=10
                                    )
                                    if resp.ok:
                                        st.success(f"'{fname}' deleted.")
                                        st.session_state["bf_files"].remove(fname)
                                        st.rerun()
                                    else:
                                        st.error(parse_error(resp))
                                except requests.ConnectionError:
                                    st.error("Cannot reach backend")
                                except Exception as e:
                                    st.error(str(e))

        # ── Add new files ──────────────────────────────────────────────────────
        st.divider()
        with st.expander("+ Add New Files"):
            upload_acl = st.selectbox(
                "Access Level",
                list(ACL_OPTIONS.keys()),
                format_func=lambda k: ACL_OPTIONS[k],
                key="bf_upload_acl",
            )
            uploaded_files = st.file_uploader("Choose files", accept_multiple_files=True, key="bf_uploader")

            if st.button("Upload", type="primary", key="bf_upload_btn"):
                if not uploaded_files:
                    st.error("Select at least one file to upload")
                else:
                    with st.spinner(f"Uploading {len(uploaded_files)} file(s) to {bf_bucket}..."):
                        try:
                            files_payload = [
                                ("files", (f.name, f.getvalue(), f.type or "application/octet-stream"))
                                for f in uploaded_files
                            ]
                            resp = requests.post(
                                f"{API}/upload",
                                files=files_payload,
                                data={"bucket_name": bf_bucket, "acl": upload_acl},
                            )
                            if resp.ok:
                                for result in resp.json()["results"]:
                                    if result["success"]:
                                        st.success(f"{result['filename']} uploaded")
                                        st.code(result["url"], language=None)
                                    else:
                                        st.error(f"{result['filename']}: {result['error']}")
                                # Reload file list to reflect newly uploaded files
                                refresh = requests.get(f"{API}/list-objects/{bf_bucket}", timeout=10)
                                if refresh.ok:
                                    st.session_state["bf_files"] = refresh.json()["objects"]
                                    st.session_state["bf_bucket_loaded"] = bf_bucket
                                st.rerun()
                            else:
                                st.error(parse_error(resp))
                        except requests.ConnectionError:
                            st.error("Cannot reach backend — make sure `uvicorn backend:app --reload` is running")
                        except Exception as e:
                            st.error(str(e))

# ── Tab 3: Change Access Level ────────────────────────────────────────────────

with tab3:
    st.header("Change Object Access Level")

    buckets = st.session_state.get("buckets", [])

    if buckets:
        acl_bucket = st.selectbox("Select Bucket", buckets, key="acl_bucket_select")
    else:
        acl_bucket = st.text_input(
            "Bucket Name",
            key="acl_bucket_text",
            placeholder="No buckets found — enter name manually",
        )
        st.caption("Click **Refresh Buckets** at the top to load your buckets.")

    if st.button("Load Objects"):
        if not acl_bucket:
            st.error("Select or enter a bucket name first")
        else:
            with st.spinner("Loading objects..."):
                try:
                    resp = requests.get(f"{API}/list-objects/{acl_bucket}")
                    if resp.ok:
                        st.session_state["objects"] = resp.json()["objects"]
                        st.session_state["acl_bucket_loaded"] = acl_bucket
                        if not st.session_state["objects"]:
                            st.info("No objects found in this bucket")
                    else:
                        st.error(parse_error(resp))
                except requests.ConnectionError:
                    st.error("Cannot reach backend — make sure `uvicorn backend:app --reload` is running")
                except Exception as e:
                    st.error(str(e))

    # Clear objects list if user switches to a different bucket
    if st.session_state.get("acl_bucket_loaded") != acl_bucket:
        st.session_state.pop("objects", None)

    if st.session_state.get("objects"):
        st.divider()
        object_key = st.selectbox("Select Object", st.session_state["objects"])
        new_acl = st.selectbox(
            "New Access Level",
            list(ACL_OPTIONS.keys()),
            format_func=lambda k: ACL_OPTIONS[k],
            key="new_acl",
        )

        if st.button("Apply Access Level", type="primary"):
            with st.spinner("Updating access level..."):
                try:
                    resp = requests.post(
                        f"{API}/change-acl",
                        data={
                            "bucket_name": acl_bucket,
                            "object_key": object_key,
                            "acl": new_acl,
                        },
                    )
                    if resp.ok:
                        st.success(resp.json()["message"])
                        st.info(f"Object: `{object_key}` — New access: **{ACL_OPTIONS[new_acl]}**")
                    else:
                        st.error(parse_error(resp))
                except requests.ConnectionError:
                    st.error("Cannot reach backend — make sure `uvicorn backend:app --reload` is running")
                except Exception as e:
                    st.error(str(e))

# ── Tab 4: Delete Bucket ──────────────────────────────────────────────────────
with tab4:
    st.header("Delete Bucket")
    st.warning("This permanently deletes the bucket and **all objects inside it**. This cannot be undone.")

    buckets = st.session_state.get("buckets", [])

    if buckets:
        del_bucket = st.selectbox("Select Bucket to Delete", buckets, key="del_bucket_select")
    else:
        del_bucket = st.text_input(
            "Bucket Name",
            key="del_bucket_text",
            placeholder="No buckets found — enter name manually",
        )
        st.caption("Click **Refresh Buckets** at the top to load your buckets.")

    st.markdown("Type the bucket name below to confirm deletion:")
    confirm_name = st.text_input("Confirm bucket name", placeholder=del_bucket or "bucket-name")

    confirmed = confirm_name == del_bucket and bool(del_bucket)

    if not confirmed and confirm_name:
        st.error("Name does not match — check your spelling.")

    if st.button("Delete Bucket", type="primary", disabled=not confirmed):
        with st.spinner(f"Deleting '{del_bucket}' and all its contents..."):
            try:
                resp = requests.delete(f"{API}/delete-bucket/{del_bucket}")
                if resp.ok:
                    st.success(resp.json()["message"])
                    load_buckets()
                    st.rerun()
                else:
                    st.error(parse_error(resp))
            except requests.ConnectionError:
                st.error("Cannot reach backend — make sure `uvicorn backend:app --reload` is running")
            except Exception as e:
                st.error(str(e))
