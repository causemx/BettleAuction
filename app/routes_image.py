from fastapi import APIRouter, UploadFile, Depends, File, HTTPException
from fastapi.responses import JSONResponse
import os
import uuid


router_img = APIRouter(prefix="/images", tags=["images"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

@router_img.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Invalid format")
     # Generate unique filename
    filename = f"{uuid.uuid4()}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    
    # Save file
    contents = await file.read()
    with open(filepath, "wb") as f:
        f.write(contents)
    
    return JSONResponse({
        "filename": filename,
        "size": len(contents),
        "path": filepath
    })