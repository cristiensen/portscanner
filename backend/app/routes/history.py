from fastapi import APIRouter
from ..database import get_history, clear_history

router = APIRouter(prefix="/api/history", tags=["history"])

@router.get("/")
async def list_history(limit: int = 50):
    history = await get_history(limit)
    return {"history": [h.model_dump() for h in history]}

@router.delete("/")
async def wipe_history():
    await clear_history()
    return {"cleared": True}