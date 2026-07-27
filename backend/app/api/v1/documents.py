from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, Request, Response, UploadFile
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.sensitive_actions import handle_sensitive_action
from app.core import approval_actions
from app.core.database import get_db
from app.models.enums import EntityType
from app.models.user import User
from app.schemas.document import (
    DocumentDetail,
    DocumentListResponse,
    DocumentShareCreate,
    DocumentShareResponse,
    DocumentUpdate,
    SharedDocumentResponse,
)
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=DocumentListResponse)
def list_documents(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    entity_type: EntityType | None = None,
    entity_id: UUID | None = None,
    document_type_id: UUID | None = None,
    building_id: UUID | None = None,
    search: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    is_archived: bool | None = None,
) -> DocumentListResponse:
    from datetime import date as date_type

    return DocumentService(db).list_documents(
        current_user,
        page=page,
        page_size=page_size,
        entity_type=entity_type,
        entity_id=entity_id,
        document_type_id=document_type_id,
        building_id=building_id,
        search=search,
        date_from=date_type.fromisoformat(date_from) if date_from else None,
        date_to=date_type.fromisoformat(date_to) if date_to else None,
        is_archived=is_archived,
    )


@router.post("", response_model=DocumentDetail, status_code=201)
def upload_document(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    document_type_id: Annotated[str, Form()],
    title: Annotated[str, Form()],
    entity_type: Annotated[EntityType, Form()],
    entity_id: Annotated[str, Form()],
    file: UploadFile = File(...),
    description: Annotated[str | None, Form()] = None,
) -> DocumentDetail:
    return DocumentService(db).upload_document(
        current_user,
        document_type_id=UUID(document_type_id),
        title=title,
        entity_type=entity_type,
        entity_id=UUID(entity_id),
        file=file,
        description=description,
    )


@router.get("/shared/{token}", response_model=SharedDocumentResponse)
def get_shared_document(
    token: str,
    db: Annotated[Session, Depends(get_db)],
) -> SharedDocumentResponse:
    response, _ = DocumentService(db).get_shared_document(token)
    return response


@router.get("/shared/{token}/download")
def download_shared_document(
    token: str,
    db: Annotated[Session, Depends(get_db)],
) -> FileResponse:
    path, document = DocumentService(db).get_shared_file_path(token)
    return FileResponse(
        path,
        media_type=document.mime_type,
        filename=document.file_name,
    )


@router.get("/{document_id}", response_model=DocumentDetail)
def get_document(
    document_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> DocumentDetail:
    return DocumentService(db).get_document(current_user, document_id)


@router.patch("/{document_id}", response_model=DocumentDetail)
def update_document(
    document_id: UUID,
    payload: DocumentUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> DocumentDetail:
    return DocumentService(db).update_document(current_user, document_id, payload)


@router.delete("/{document_id}")
def delete_document(
    document_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    http_request: Request,
    reason: str | None = Query(default=None),
):
    result = handle_sensitive_action(
        db,
        current_user,
        action_code=approval_actions.DOCUMENT_DELETE,
        entity_type="document",
        entity_id=str(document_id),
        reason=reason,
        http_request=http_request,
        execute_direct=lambda: DocumentService(db).delete_document(current_user, document_id),
    )
    if result:
        return JSONResponse(status_code=202, content=jsonable_encoder(result))
    return Response(status_code=204)


@router.get("/{document_id}/download")
def download_document(
    document_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> FileResponse:
    path, document = DocumentService(db).get_file_path(current_user, document_id)
    return FileResponse(
        path,
        media_type=document.mime_type,
        filename=document.file_name,
    )


@router.get("/{document_id}/preview")
def preview_document(
    document_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> FileResponse:
    path, document = DocumentService(db).get_file_path(current_user, document_id, preview=True)
    return FileResponse(
        path,
        media_type=document.mime_type,
        headers={"Content-Disposition": f'inline; filename="{document.file_name}"'},
    )


@router.post("/{document_id}/share", response_model=DocumentShareResponse)
def share_document(
    document_id: UUID,
    payload: DocumentShareCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> DocumentShareResponse:
    return DocumentService(db).create_share(current_user, document_id, payload)
