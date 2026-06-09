# Lab 1 — Amazon S3 Manager

A web app to create buckets, upload files, and manage object access levels on AWS S3.  
Built with **FastAPI** (backend) and **Streamlit** (frontend).

---

## Prerequisites

- Python 3.10+
- AWS Academy lab session with active credentials

Install dependencies:

```bash
pip install fastapi uvicorn streamlit boto3 python-dotenv python-multipart
```

---

## Configuration

Create or update the `.env` file in this folder with your AWS Academy credentials:

```env
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_SESSION_TOKEN=your_session_token
AWS_DEFAULT_REGION=us-east-1
```

> Get these from your AWS Academy lab: **AWS Details → Show → Copy credentials**

---

## Running the App

Open **two terminals** in this folder.

**Terminal 1 — Backend:**

```bash
uvicorn backend:app --reload --port 8000
```

**Terminal 2 — Frontend:**

```bash
streamlit run app.py --server.port 8501
```

Then open **http://localhost:8501** in your browser.

---

## Stopping the App

Press `Ctrl+C` in each terminal, or run:

```bash
fuser -k 8000/tcp 8501/tcp
```
