from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter(tags=["dashboard"])

STATIC_DIR = Path(__file__).resolve().parent.parent.parent / "static"


@router.get("/dashboard")
async def dashboard() -> FileResponse:
    return FileResponse(STATIC_DIR / "dashboard.html", media_type="text/html")
