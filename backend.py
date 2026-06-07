from fastapi import FastAPI, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pathlib import Path
import upload_to_s3 as s3

load_dotenv(dotenv_path=Path(__file__).parent / ".env")

app = FastAPI(title="S3 Manager API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/create-bucket")
async def create_bucket(
    bucket_name: str = Form(...),
    region: str = Form("us-east-1"),
    allow_public: str = Form("false"),
):
    public = allow_public.lower() in ("true", "1", "yes")
    success, error = s3.create_bucket(bucket_name, region, public)
    if not success:
        raise HTTPException(status_code=400, detail=error)
    return {"message": f"Bucket '{bucket_name}' created successfully in {region}"}


@app.get("/list-buckets")
async def list_buckets():
    buckets, error = s3.list_buckets()
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {"buckets": buckets}


@app.delete("/delete-bucket/{bucket_name}")
async def delete_bucket(bucket_name: str):
    success, error = s3.delete_bucket(bucket_name)
    if not success:
        raise HTTPException(status_code=400, detail=error)
    return {"message": f"Bucket '{bucket_name}' and all its contents deleted successfully"}
