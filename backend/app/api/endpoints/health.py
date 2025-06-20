from fastapi import APIRouter
from app.core.config import settings
from datetime import datetime

router = APIRouter()

@router.get("/")
async def health_check():
    return {
        "service": "DocProc",
        "status": "OK",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "environment": settings.ENVIRONMENT,
    }
