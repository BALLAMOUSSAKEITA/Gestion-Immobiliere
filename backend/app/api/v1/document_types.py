from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.document import DocumentTypeResponse
from app.services.document_service import DocumentService

router = APIRouter(prefix="/document-types", tags=["document-types"])


@router.get("", response_model=list[DocumentTypeResponse])
def list_document_types(
    _: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[DocumentTypeResponse]:
    return DocumentService(db).list_types()
