from fastapi import APIRouter, HTTPException
from ..models import PresetModel
from ..database import get_presets, save_preset, delete_preset

router = APIRouter(prefix="/api/presets", tags=["presets"])

@router.get("/")
async def list_presets():
    presets = await get_presets()
    return {"presets": [p.model_dump() for p in presets]}

@router.post("/")
async def create_preset(preset: PresetModel):
    if not preset.name.strip():
        raise HTTPException(status_code=400, detail="Preset name cannot be empty")
    saved = await save_preset(preset)
    return saved.model_dump()

@router.delete("/{preset_id}")
async def remove_preset(preset_id: str):
    deleted = await delete_preset(preset_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Preset not found")
    return {"deleted": True}