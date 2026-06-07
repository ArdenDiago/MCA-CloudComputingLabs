from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from typing import List
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


@app.post("/upload")
async def upload_files(
    files: List[UploadFile] = File(...),
    bucket_name: str = Form(...),
    acl: str = Form("private"),
):
    results = []
    for file in files:
        content = await file.read()
        success, url, error = s3.upload_file(
            content,
            bucket_name,
            file.filename,
            acl,
            file.content_type or "application/octet-stream",
        )
        results.append({"filename": file.filename, "success": success, "url": url, "error": error})
    return {"results": results}


@app.get("/list-objects/{bucket_name}")
async def list_objects(bucket_name: str):
    objects, error = s3.list_objects(bucket_name)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {"objects": objects}


@app.delete("/delete-object/{bucket_name}/{object_key:path}")
async def delete_object(bucket_name: str, object_key: str):
    success, error = s3.delete_object(bucket_name, object_key)
    if not success:
        raise HTTPException(status_code=400, detail=error)
    return {"message": f"'{object_key}' deleted from '{bucket_name}' successfully"}


@app.get("/get-object-url/{bucket_name}/{object_key:path}")
async def get_object_url(bucket_name: str, object_key: str):
    url, error = s3.get_presigned_url(bucket_name, object_key)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {"url": url}


@app.post("/change-acl")
async def change_acl(
    bucket_name: str = Form(...),
    object_key: str = Form(...),
    acl: str = Form(...),
):
    success, error = s3.change_object_acl(bucket_name, object_key, acl)
    if not success:
        raise HTTPException(status_code=400, detail=error)
    return {"message": f"Access level for '{object_key}' changed to '{acl}' successfully"}
