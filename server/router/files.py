from fastapi import APIRouter, UploadFile, File, HTTPException
import shutil
import os
from pathlib import Path
from typing import List

router = APIRouter(
    prefix="/files",
    tags=["files"],
)

# 用户指定的文件保存目录
UPLOAD_DIR = Path("/Users/zroc/Desktop/Zroc/AI/mm-llms-surveillance-analysis/server/files")

# 确保目录存在
if not UPLOAD_DIR.exists():
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    上传图片文件
    """
    # 检查文件扩展名
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}")

    # 构建保存路径
    file_location = UPLOAD_DIR / file.filename
    
    # 如果文件已存在，可以考虑重命名，这里简单起见直接覆盖或由用户决定
    # 为了避免文件名冲突，这里可以使用 uuid 或者时间戳，但用户没提，暂时直接用原文件名
    
    try:
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {str(e)}")
    
    return {
        "filename": file.filename,
        "saved_path": str(file_location),
        "message": "File uploaded successfully"
    }
