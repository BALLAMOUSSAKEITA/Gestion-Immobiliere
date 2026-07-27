from fastapi import APIRouter

from app.core.config import get_settings
from app.schemas.common import MessageResponse

router = APIRouter()
settings = get_settings()


@router.get("/", response_model=MessageResponse)
def root() -> MessageResponse:
    return MessageResponse(message="Gestion Immobilière API")
