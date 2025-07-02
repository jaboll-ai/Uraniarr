from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from backend.dependencies import get_session
from backend.services.author_service import import_author


router = APIRouter(prefix="/mapi", tags=["middleware"])

@router.post("/author/{author_id}")
def mapi_import_author(author_id: str, session: Session = Depends(get_session), override: bool = False):
    return import_author(author_id, session, override)
