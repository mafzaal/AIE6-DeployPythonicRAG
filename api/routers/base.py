from fastapi import APIRouter, Request, Response
from fastapi.responses import FileResponse
import os

from api.config import API_VERSION, BUILD_DATE, STATIC_DIR
from api.utils.user import get_or_create_user_id

router = APIRouter()

@router.get("/")
async def read_root():
    """Serve the frontend index page"""
    return FileResponse(f"{STATIC_DIR}/index.html")

@router.get("/version")
async def get_version():
    """Get API version information"""
    return {
        "api_version": API_VERSION,
        "build_date": BUILD_DATE,
        "status": "operational"
    }

@router.get("/identify")
async def identify_user(request: Request, response: Response):
    """Identify the current user or create a new user ID"""
    user_id = get_or_create_user_id(request, response)
    return {"user_id": user_id}

@router.get("/{path:path}")
async def catch_all(path: str):
    """Catch-all route to serve static files or fall back to index.html"""
    if path.startswith("static/"):
        path = path[7:]  # Remove 'static/' prefix
        
    file_path = f"{STATIC_DIR}/{path}"
    
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return FileResponse(f"{STATIC_DIR}/index.html") 