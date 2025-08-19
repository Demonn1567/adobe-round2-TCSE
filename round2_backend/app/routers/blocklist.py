from fastapi import APIRouter
from pydantic import BaseModel
from app.services.blocklist import list_ids, add, remove, clear

router = APIRouter(prefix="/admin/blocklist", tags=["admin"])

class Ids(BaseModel):
    docIds: list[str] = []

@router.get("")
def get_blocklist():
    return {"docIds": list_ids()}

@router.post("/add")
def add_blocked(payload: Ids):
    return {"docIds": add(payload.docIds)}

@router.post("/remove")
def remove_blocked(payload: Ids):
    return {"docIds": remove(payload.docIds)}

@router.post("/clear")
def clear_blocked():
    clear()
    return {"ok": True}
