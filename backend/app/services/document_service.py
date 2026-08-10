import secrets
from datetime import UTC, date, datetime, timedelta
from math import ceil
from uuid import UUID

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.core.config import get_settings
from app.core.permissions import Permission, role_has_permission
from app.models.building import Building, Unit
from app.models.document import Document, DocumentShare, DocumentType
from app.models.enums import EntityType, LeaseStatus
from app.models.expense import Expense
from app.models.payment import Payment, Receipt
from app.models.repair import Repair
from app.models.tenant import Lease, Tenant
from app.models.user import User
from app.schemas.document import (
    DocumentDetail,
    DocumentListResponse,
    DocumentShareCreate,
    DocumentShareResponse,
    DocumentSummary,
    DocumentTypeResponse,
    DocumentUpdate,
    SharedDocumentResponse,
)
from app.services.building_service import BuildingAccessService
from app.services.storage_service import StorageService
from app.services.tenant_access_service import TenantAccessService


class DocumentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        settings = get_settings()
        self.storage = StorageService()
        self.share_expiry_days = settings.document_share_expiry_days
        self.share_max_access = settings.document_share_max_access

    def list_types(self) -> list[DocumentTypeResponse]:
        types = self.db.query(DocumentType).order_by(DocumentType.label).all()
        return [
            DocumentTypeResponse(id=str(item.id), code=item.code, label=item.label)
            for item in types
        ]

    def list_documents(
        self,
        actor: User,
        page: int = 1,
        page_size: int = 20,
        entity_type: EntityType | None = None,
        entity_id: UUID | None = None,
        document_type_id: UUID | None = None,
        building_id: UUID | None = None,
        search: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        is_archived: bool | None = None,
    ) -> DocumentListResponse:
        self._ensure_read_access(actor)
        query = self._accessible_query(actor)

        if entity_type and entity_id:
            self._ensure_entity_access(actor, entity_type, entity_id)
            query = query.filter(
                Document.entity_type == entity_type,
                Document.entity_id == entity_id,
            )
        if document_type_id:
            query = query.filter(Document.document_type_id == document_type_id)
        if building_id:
            BuildingAccessService.ensure_building_access(self.db, actor, building_id)
            query = self._filter_by_building(query, building_id)
        if search:
            query = query.filter(
                or_(
                    Document.title.ilike(f"%{search}%"),
                    Document.description.ilike(f"%{search}%"),
                )
            )
        if date_from:
            query = query.filter(func.date(Document.uploaded_at) >= date_from)
        if date_to:
            query = query.filter(func.date(Document.uploaded_at) <= date_to)
        if is_archived is not None:
            query = query.filter(Document.is_archived.is_(is_archived))

        query = query.order_by(Document.uploaded_at.desc())
        total = query.count()
        records = (
            query.options(
                joinedload(Document.document_type),
                joinedload(Document.uploader),
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        pages = ceil(total / page_size) if total else 0
        return DocumentListResponse(
            items=[self._to_summary(item) for item in records],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    def get_document(self, actor: User, document_id: UUID) -> DocumentDetail:
        self._ensure_read_access(actor)
        document = self._get_or_404(document_id)
        self._ensure_entity_access(actor, document.entity_type, document.entity_id)
        return self._to_detail(document)

    def upload_document(
        self,
        actor: User,
        document_type_id: UUID,
        title: str,
        entity_type: EntityType,
        entity_id: UUID,
        file: UploadFile,
        description: str | None = None,
    ) -> DocumentDetail:
        self._ensure_manage_access(actor)
        self._ensure_entity_access(actor, entity_type, entity_id, for_write=True)
        doc_type = self._get_type_or_404(document_type_id)

        file_url, file_name, file_size, mime_type = self.storage.save_upload(
            file, entity_type, str(entity_id)
        )
        document = Document(
            document_type_id=doc_type.id,
            title=title.strip(),
            description=description.strip() if description else None,
            file_url=file_url,
            file_name=file_name,
            file_size=file_size,
            mime_type=mime_type,
            entity_type=entity_type,
            entity_id=entity_id,
            uploaded_by=actor.id,
        )
        self.db.add(document)
        self._sync_legacy_url(document)
        self.db.commit()
        recipient_ids = self._notification_recipients(entity_type, entity_id)
        if recipient_ids:
            from app.services.notification_hooks import notify_document_uploaded

            notify_document_uploaded(self.db, recipient_ids, document.title)
        return self._to_detail(self._get_or_404(document.id))

    def update_document(
        self, actor: User, document_id: UUID, payload: DocumentUpdate
    ) -> DocumentDetail:
        self._ensure_manage_access(actor)
        document = self._get_or_404(document_id)
        self._ensure_entity_access(actor, document.entity_type, document.entity_id, for_write=True)
        if payload.title is not None:
            document.title = payload.title.strip()
        if payload.description is not None:
            document.description = payload.description
        if payload.is_archived is not None:
            document.is_archived = payload.is_archived
        if payload.expires_at is not None:
            document.expires_at = payload.expires_at
        self.db.commit()
        return self._to_detail(self._get_or_404(document_id))

    def delete_document(self, actor: User, document_id: UUID) -> None:
        if actor.role.code != "super_admin":
            raise HTTPException(status_code=403, detail="Accès non autorisé")
        document = self._get_or_404(document_id)
        self.storage.delete_file(document.file_url)
        self.db.delete(document)
        self.db.commit()

    def get_file_path(self, actor: User, document_id: UUID, preview: bool = False):
        self._ensure_read_access(actor)
        document = self._get_or_404(document_id)
        self._ensure_entity_access(actor, document.entity_type, document.entity_id)
        path = self.storage.resolve_path(document.file_url)
        return path, document

    def create_share(
        self, actor: User, document_id: UUID, payload: DocumentShareCreate
    ) -> DocumentShareResponse:
        self._ensure_manage_access(actor)
        document = self._get_or_404(document_id)
        self._ensure_entity_access(actor, document.entity_type, document.entity_id, for_write=True)
        expires_days = payload.expires_in_days or self.share_expiry_days
        max_access = payload.max_access or self.share_max_access
        token = secrets.token_urlsafe(32)
        share = DocumentShare(
            document_id=document.id,
            share_token=token,
            expires_at=datetime.now(UTC) + timedelta(days=expires_days),
            created_by=actor.id,
            max_access=max_access,
        )
        self.db.add(share)
        self.db.commit()
        self.db.refresh(share)
        return DocumentShareResponse(
            id=str(share.id),
            share_token=share.share_token,
            share_url=f"/documents/shared/{share.share_token}",
            expires_at=share.expires_at,
            max_access=share.max_access,
            accessed_count=share.accessed_count,
        )

    def _is_share_expired(self, expires_at: datetime) -> bool:
        now = datetime.now(UTC)
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        return expires_at < now

    def get_shared_document(self, token: str) -> tuple[SharedDocumentResponse, Document]:
        share = (
            self.db.query(DocumentShare)
            .options(joinedload(DocumentShare.document))
            .filter(DocumentShare.share_token == token)
            .first()
        )
        if share is None:
            raise HTTPException(status_code=404, detail="Lien de partage invalide")
        if self._is_share_expired(share.expires_at):
            raise HTTPException(status_code=410, detail="Lien de partage expiré")
        if share.accessed_count >= share.max_access:
            raise HTTPException(status_code=410, detail="Nombre d'accès maximum atteint")

        share.accessed_count += 1
        self.db.commit()
        document = share.document
        response = SharedDocumentResponse(
            title=document.title,
            file_name=document.file_name,
            mime_type=document.mime_type,
            file_size=document.file_size,
            download_url=f"/api/v1/documents/shared/{token}/download",
        )
        return response, document

    def get_shared_file_path(self, token: str):
        share = (
            self.db.query(DocumentShare)
            .options(joinedload(DocumentShare.document))
            .filter(DocumentShare.share_token == token)
            .first()
        )
        if share is None:
            raise HTTPException(status_code=404, detail="Lien de partage invalide")
        if self._is_share_expired(share.expires_at):
            raise HTTPException(status_code=410, detail="Lien de partage expiré")
        if share.accessed_count >= share.max_access:
            raise HTTPException(status_code=410, detail="Nombre d'accès maximum atteint")
        return self.storage.resolve_path(share.document.file_url), share.document

    def _accessible_query(self, actor: User):
        query = self.db.query(Document)
        if actor.role.code in ("super_admin", "admin_familial"):
            return query
        if actor.role.code == "gestionnaire":
            allowed = BuildingAccessService.accessible_building_ids(self.db, actor) or set()
            if not allowed:
                return query.filter(Document.id.is_(None))
            return self._filter_by_building(query, allowed_buildings=allowed)
        if actor.role.code == "proprietaire":
            allowed = BuildingAccessService.accessible_building_ids(self.db, actor) or set()
            owner_id = BuildingAccessService.get_owner_profile_id(actor)
            filters = []
            if allowed:
                filters.append(self._building_filter_clause(allowed))
            if owner_id:
                filters.append(
                    (Document.entity_type == EntityType.owner_profile)
                    & (Document.entity_id == owner_id)
                )
            if not filters:
                return query.filter(Document.id.is_(None))
            return query.filter(or_(*filters))
        if actor.role.code == "locataire":
            return self._filter_for_tenant(query, actor)
        return query.filter(Document.id.is_(None))

    def _filter_for_tenant(self, query, actor: User):
        if actor.tenant_profile is None:
            return query.filter(Document.id.is_(None))
        tenant_id = actor.tenant_profile.id
        lease_ids = [
            row[0]
            for row in self.db.query(Lease.id)
            .filter(Lease.tenant_id == tenant_id)
            .all()
        ]
        receipt_ids = [
            row[0]
            for row in self.db.query(Receipt.id)
            .join(Payment)
            .filter(Payment.tenant_id == tenant_id)
            .all()
        ]
        clauses = [
            (Document.entity_type == EntityType.tenant) & (Document.entity_id == tenant_id),
        ]
        if lease_ids:
            clauses.append(
                (Document.entity_type == EntityType.lease) & (Document.entity_id.in_(lease_ids))
            )
        if receipt_ids:
            clauses.append(
                (Document.entity_type == EntityType.receipt) & (Document.entity_id.in_(receipt_ids))
            )
        return query.filter(or_(*clauses))

    def _filter_by_building(self, query, building_id: UUID | None = None, allowed_buildings: set[UUID] | None = None):
        if building_id:
            return query.filter(self._building_filter_clause({building_id}))
        if allowed_buildings:
            return query.filter(self._building_filter_clause(allowed_buildings))
        return query

    def _building_filter_clause(self, building_ids: set[UUID]):
        unit_ids = [
            row[0]
            for row in self.db.query(Unit.id).filter(Unit.building_id.in_(building_ids)).all()
        ]
        lease_ids = [
            row[0]
            for row in self.db.query(Lease.id).join(Unit).filter(Unit.building_id.in_(building_ids)).all()
        ]
        clauses = [
            (Document.entity_type == EntityType.building) & (Document.entity_id.in_(building_ids)),
        ]
        if unit_ids:
            clauses.append(
                (Document.entity_type == EntityType.unit) & (Document.entity_id.in_(unit_ids))
            )
        if lease_ids:
            clauses.append(
                (Document.entity_type == EntityType.lease) & (Document.entity_id.in_(lease_ids))
            )
        return or_(*clauses)

    def _ensure_entity_access(
        self,
        actor: User,
        entity_type: EntityType,
        entity_id: UUID,
        for_write: bool = False,
    ) -> None:
        if actor.role.code == "visiteur":
            raise HTTPException(status_code=403, detail="Accès non autorisé")
        if for_write and not role_has_permission(actor.role.code, Permission.DOCUMENTS_MANAGE):
            if actor.role.code != "super_admin":
                raise HTTPException(status_code=403, detail="Accès non autorisé")

        if entity_type == EntityType.building:
            BuildingAccessService.ensure_building_access(self.db, actor, entity_id)
        elif entity_type == EntityType.unit:
            TenantAccessService.ensure_unit_access(self.db, actor, entity_id)
        elif entity_type == EntityType.tenant:
            if actor.role.code == "locataire":
                if actor.tenant_profile is None or actor.tenant_profile.id != entity_id:
                    raise HTTPException(status_code=403, detail="Accès non autorisé")
            else:
                TenantAccessService.ensure_tenant_access(self.db, actor, entity_id)
        elif entity_type == EntityType.lease:
            lease = self.db.query(Lease).options(joinedload(Lease.unit)).filter(Lease.id == entity_id).first()
            if lease is None:
                raise HTTPException(status_code=404, detail="Bail introuvable")
            if actor.role.code == "locataire":
                if actor.tenant_profile is None or lease.tenant_id != actor.tenant_profile.id:
                    raise HTTPException(status_code=403, detail="Accès non autorisé")
            else:
                BuildingAccessService.ensure_building_access(self.db, actor, lease.unit.building_id)
        elif entity_type == EntityType.payment:
            payment = (
                self.db.query(Payment)
                .options(joinedload(Payment.lease).joinedload(Lease.unit))
                .filter(Payment.id == entity_id)
                .first()
            )
            if payment is None:
                raise HTTPException(status_code=404, detail="Paiement introuvable")
            if actor.role.code == "locataire":
                if actor.tenant_profile is None or payment.tenant_id != actor.tenant_profile.id:
                    raise HTTPException(status_code=403, detail="Accès non autorisé")
            else:
                BuildingAccessService.ensure_building_access(self.db, actor, payment.lease.unit.building_id)
        elif entity_type == EntityType.expense:
            expense = self.db.query(Expense).filter(Expense.id == entity_id).first()
            if expense is None:
                raise HTTPException(status_code=404, detail="Dépense introuvable")
            if expense.building_id:
                BuildingAccessService.ensure_building_access(self.db, actor, expense.building_id)
        elif entity_type == EntityType.repair:
            repair = self.db.query(Repair).filter(Repair.id == entity_id).first()
            if repair is None:
                raise HTTPException(status_code=404, detail="Réparation introuvable")
            BuildingAccessService.ensure_building_access(self.db, actor, repair.building_id)
        elif entity_type == EntityType.owner_profile:
            if actor.role.code == "proprietaire":
                owner_id = BuildingAccessService.get_owner_profile_id(actor)
                if owner_id != entity_id:
                    raise HTTPException(status_code=403, detail="Accès non autorisé")
            elif actor.role.code not in ("super_admin", "admin_familial", "gestionnaire"):
                raise HTTPException(status_code=403, detail="Accès non autorisé")
        elif entity_type == EntityType.receipt:
            receipt = (
                self.db.query(Receipt)
                .options(joinedload(Receipt.payment).joinedload(Payment.lease).joinedload(Lease.unit))
                .filter(Receipt.id == entity_id)
                .first()
            )
            if receipt is None:
                raise HTTPException(status_code=404, detail="Reçu introuvable")
            if actor.role.code == "locataire":
                if actor.tenant_profile is None or receipt.payment.tenant_id != actor.tenant_profile.id:
                    raise HTTPException(status_code=403, detail="Accès non autorisé")
            else:
                BuildingAccessService.ensure_building_access(
                    self.db, actor, receipt.payment.lease.unit.building_id
                )

    def _sync_legacy_url(self, document: Document) -> None:
        from app.core.document_types_seed import LEASE_CONTRACT_TYPE_ID

        if document.entity_type == EntityType.lease and document.document_type_id == LEASE_CONTRACT_TYPE_ID:
            lease = self.db.query(Lease).filter(Lease.id == document.entity_id).first()
            if lease:
                lease.contract_document_url = document.file_url

    def _notification_recipients(self, entity_type: EntityType, entity_id: UUID) -> list[UUID]:
        from uuid import UUID as UUIDType

        recipients: list[UUIDType] = []
        if entity_type == EntityType.tenant:
            tenant = self.db.query(Tenant).filter(Tenant.id == entity_id).first()
            if tenant and tenant.user_id:
                recipients.append(tenant.user_id)
        elif entity_type == EntityType.lease:
            lease = self.db.query(Lease).filter(Lease.id == entity_id).first()
            if lease:
                tenant = self.db.query(Tenant).filter(Tenant.id == lease.tenant_id).first()
                if tenant and tenant.user_id:
                    recipients.append(tenant.user_id)
        return recipients

    def _get_or_404(self, document_id: UUID) -> Document:
        document = (
            self.db.query(Document)
            .options(joinedload(Document.document_type), joinedload(Document.uploader))
            .filter(Document.id == document_id)
            .first()
        )
        if document is None:
            raise HTTPException(status_code=404, detail="Document introuvable")
        return document

    def _get_type_or_404(self, type_id: UUID) -> DocumentType:
        doc_type = self.db.query(DocumentType).filter(DocumentType.id == type_id).first()
        if doc_type is None:
            raise HTTPException(status_code=404, detail="Type de document introuvable")
        return doc_type

    def _ensure_read_access(self, actor: User) -> None:
        if role_has_permission(actor.role.code, Permission.DOCUMENTS_READ):
            return
        raise HTTPException(status_code=403, detail="Accès non autorisé")

    def _ensure_manage_access(self, actor: User) -> None:
        if role_has_permission(actor.role.code, Permission.DOCUMENTS_MANAGE):
            return
        raise HTTPException(status_code=403, detail="Accès non autorisé")

    def _to_summary(self, document: Document) -> DocumentSummary:
        return DocumentSummary(
            id=str(document.id),
            document_type_code=document.document_type.code,
            document_type_label=document.document_type.label,
            title=document.title,
            description=document.description,
            file_name=document.file_name,
            file_size=document.file_size,
            mime_type=document.mime_type,
            entity_type=document.entity_type,
            entity_id=str(document.entity_id),
            uploaded_by_name=f"{document.uploader.first_name} {document.uploader.last_name}",
            uploaded_at=document.uploaded_at,
            is_archived=document.is_archived,
            expires_at=document.expires_at,
        )

    def _to_detail(self, document: Document) -> DocumentDetail:
        summary = self._to_summary(document)
        return DocumentDetail(
            **summary.model_dump(),
            file_url=document.file_url,
            updated_at=document.updated_at,
        )
