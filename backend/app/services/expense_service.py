import shutil
from datetime import UTC, date, datetime
from decimal import Decimal
from math import ceil
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.core.config import get_settings
from app.models.building import Building, Unit
from app.models.enums import ExpenseStatus, PaymentMethod
from app.models.expense import Expense, ExpenseCategory
from app.models.user import User
from app.schemas.expense import (
    ExpenseCategoryBreakdown,
    ExpenseCategoryResponse,
    ExpenseCreate,
    ExpenseDetail,
    ExpenseListResponse,
    ExpenseSummaryItem,
    ExpenseSummaryResponse,
    ExpenseUpdate,
)
from app.core.permissions import Permission, role_has_permission
from app.services.building_service import BuildingAccessService


class ExpenseService:
    REPORTABLE_STATUSES = (ExpenseStatus.recorded, ExpenseStatus.validated)

    def __init__(self, db: Session) -> None:
        self.db = db
        settings = get_settings()
        self.upload_dir = Path(settings.upload_dir)
        self.validation_threshold = Decimal(str(settings.expense_validation_threshold))

    def list_categories(self) -> list[ExpenseCategoryResponse]:
        categories = (
            self.db.query(ExpenseCategory)
            .filter(ExpenseCategory.is_active.is_(True))
            .order_by(ExpenseCategory.label)
            .all()
        )
        return [self._category_to_response(item) for item in categories]

    def list_expenses(
        self,
        actor: User,
        page: int = 1,
        page_size: int = 20,
        building_id: UUID | None = None,
        unit_id: UUID | None = None,
        owner_profile_id: UUID | None = None,
        category_id: UUID | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        min_amount: Decimal | None = None,
        max_amount: Decimal | None = None,
        payment_method: PaymentMethod | None = None,
        supplier: str | None = None,
        status_filter: ExpenseStatus | None = None,
    ) -> ExpenseListResponse:
        self._ensure_read_access(actor)
        query = self._base_query(actor)

        if building_id:
            BuildingAccessService.ensure_building_access(self.db, actor, building_id)
            query = query.filter(Expense.building_id == building_id)
        if unit_id:
            unit = self.db.query(Unit).filter(Unit.id == unit_id).first()
            if unit:
                BuildingAccessService.ensure_building_access(self.db, actor, unit.building_id)
            query = query.filter(Expense.unit_id == unit_id)
        if owner_profile_id:
            query = query.filter(Expense.owner_profile_id == owner_profile_id)
        if category_id:
            query = query.filter(Expense.category_id == category_id)
        if date_from:
            query = query.filter(Expense.expense_date >= date_from)
        if date_to:
            query = query.filter(Expense.expense_date <= date_to)
        if min_amount is not None:
            query = query.filter(Expense.amount >= min_amount)
        if max_amount is not None:
            query = query.filter(Expense.amount <= max_amount)
        if payment_method:
            query = query.filter(Expense.payment_method == payment_method)
        if supplier:
            query = query.filter(Expense.supplier_name.ilike(f"%{supplier}%"))
        if status_filter:
            query = query.filter(Expense.status == status_filter)

        query = query.order_by(Expense.expense_date.desc(), Expense.created_at.desc())
        total = query.count()
        records = query.offset((page - 1) * page_size).limit(page_size).all()
        pages = ceil(total / page_size) if total else 0
        return ExpenseListResponse(
            items=[self._to_summary(item) for item in records],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    def get_expense(self, actor: User, expense_id: UUID) -> ExpenseDetail:
        self._ensure_read_access(actor)
        expense = self._get_or_404(expense_id)
        self._ensure_expense_access(actor, expense)
        return self._to_detail(expense)

    def create_expense(self, actor: User, payload: ExpenseCreate) -> ExpenseDetail:
        self._ensure_manage_access(actor)
        category = self._get_category_or_404(UUID(payload.category_id))
        building_id, unit_id, owner_profile_id = self._resolve_links(payload)
        self._ensure_link_access(actor, building_id, unit_id, owner_profile_id)

        amount = payload.amount
        requires_validation = amount >= self.validation_threshold
        expense_status = (
            ExpenseStatus.pending_validation if requires_validation else ExpenseStatus.recorded
        )

        expense = Expense(
            category_id=category.id,
            building_id=building_id,
            unit_id=unit_id,
            owner_profile_id=owner_profile_id,
            supplier_name=payload.supplier_name,
            description=payload.description.strip(),
            amount=amount,
            payment_method=payload.payment_method,
            expense_date=payload.expense_date,
            status=expense_status,
            requires_validation=requires_validation,
            recorded_by=actor.id,
        )
        self.db.add(expense)
        self.db.commit()
        return self._to_detail(self._get_or_404(expense.id))

    def update_expense(
        self, actor: User, expense_id: UUID, payload: ExpenseUpdate
    ) -> ExpenseDetail:
        self._ensure_manage_access(actor)
        expense = self._get_or_404(expense_id)
        self._ensure_expense_access(actor, expense)
        if expense.status in (ExpenseStatus.validated, ExpenseStatus.rejected):
            raise HTTPException(status_code=400, detail="Dépense non modifiable")

        if payload.category_id:
            expense.category_id = self._get_category_or_404(UUID(payload.category_id)).id
        if payload.description is not None:
            expense.description = payload.description.strip()
        if payload.supplier_name is not None:
            expense.supplier_name = payload.supplier_name
        if payload.payment_method is not None:
            expense.payment_method = payload.payment_method
        if payload.expense_date is not None:
            expense.expense_date = payload.expense_date

        if any(
            value is not None
            for value in (payload.building_id, payload.unit_id, payload.owner_profile_id)
        ):
            building_id, unit_id, owner_profile_id = self._resolve_links(
                ExpenseCreate(
                    category_id=str(expense.category_id),
                    building_id=payload.building_id,
                    unit_id=payload.unit_id,
                    owner_profile_id=payload.owner_profile_id,
                    description=expense.description,
                    amount=expense.amount,
                    payment_method=expense.payment_method,
                    expense_date=expense.expense_date,
                )
            )
            self._ensure_link_access(actor, building_id, unit_id, owner_profile_id)
            expense.building_id = building_id
            expense.unit_id = unit_id
            expense.owner_profile_id = owner_profile_id

        if payload.amount is not None:
            expense.amount = payload.amount
            expense.requires_validation = payload.amount >= self.validation_threshold
            if expense.requires_validation and expense.status == ExpenseStatus.recorded:
                expense.status = ExpenseStatus.pending_validation
            elif not expense.requires_validation and expense.status == ExpenseStatus.pending_validation:
                expense.status = ExpenseStatus.recorded

        self.db.commit()
        return self._to_detail(self._get_or_404(expense_id))

    def delete_expense(self, actor: User, expense_id: UUID) -> None:
        if actor.role.code != "super_admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès non autorisé")
        expense = self._get_or_404(expense_id)
        self.db.delete(expense)
        self.db.commit()

    def upload_receipt(
        self, actor: User, expense_id: UUID, file: UploadFile
    ) -> ExpenseDetail:
        self._ensure_manage_access(actor)
        expense = self._get_or_404(expense_id)
        self._ensure_expense_access(actor, expense)
        if expense.status in (ExpenseStatus.validated, ExpenseStatus.rejected):
            raise HTTPException(status_code=400, detail="Dépense non modifiable")

        extension = Path(file.filename or "receipt.pdf").suffix.lower() or ".pdf"
        if extension not in {".pdf", ".jpg", ".jpeg", ".png", ".webp"}:
            raise HTTPException(status_code=400, detail="Format de fichier non supporté")
        filename = f"{uuid4()}{extension}"
        target_dir = self.upload_dir / "expenses"
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / filename
        with target_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        expense.receipt_url = f"/uploads/expenses/{filename}"
        self.db.commit()
        return self._to_detail(self._get_or_404(expense_id))

    def validate_expense(self, actor: User, expense_id: UUID) -> ExpenseDetail:
        if actor.role.code != "super_admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès non autorisé")
        expense = self._get_or_404(expense_id)
        if expense.status != ExpenseStatus.pending_validation:
            raise HTTPException(status_code=400, detail="Dépense non soumise à validation")
        expense.status = ExpenseStatus.validated
        expense.validated_by = actor.id
        expense.validated_at = datetime.now(UTC)
        self.db.commit()
        return self._to_detail(self._get_or_404(expense_id))

    def reject_expense(self, actor: User, expense_id: UUID) -> ExpenseDetail:
        if actor.role.code != "super_admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès non autorisé")
        expense = self._get_or_404(expense_id)
        if expense.status != ExpenseStatus.pending_validation:
            raise HTTPException(status_code=400, detail="Dépense non soumise à validation")
        expense.status = ExpenseStatus.rejected
        expense.validated_by = actor.id
        expense.validated_at = datetime.now(UTC)
        self.db.commit()
        return self._to_detail(self._get_or_404(expense_id))

    def get_summary(
        self,
        actor: User,
        year: int | None = None,
        month: int | None = None,
        building_id: UUID | None = None,
        group_by: str = "category",
    ) -> ExpenseSummaryResponse:
        self._ensure_read_access(actor)
        query = self._base_query(actor).filter(Expense.status.in_(self.REPORTABLE_STATUSES))

        if year:
            query = query.filter(func.extract("year", Expense.expense_date) == year)
        if month:
            query = query.filter(func.extract("month", Expense.expense_date) == month)
        if building_id:
            BuildingAccessService.ensure_building_access(self.db, actor, building_id)
            query = query.filter(Expense.building_id == building_id)

        records = query.options(
            joinedload(Expense.category), joinedload(Expense.building)
        ).all()
        total_amount = sum((item.amount for item in records), Decimal("0"))
        breakdown: dict[str, ExpenseCategoryBreakdown] = {}

        for record in records:
            if group_by == "building":
                key = record.building.name if record.building else "Sans immeuble"
            elif group_by == "month":
                key = f"{record.expense_date.year}-{record.expense_date.month:02d}"
            else:
                key = record.category.label

            if key not in breakdown:
                breakdown[key] = ExpenseCategoryBreakdown(category=key, amount=Decimal("0"), count=0)
            breakdown[key].amount += record.amount
            breakdown[key].count += 1

        return ExpenseSummaryResponse(
            total_amount=total_amount,
            count=len(records),
            by_category=sorted(breakdown.values(), key=lambda item: item.amount, reverse=True),
        )

    def _base_query(self, actor: User):
        query = (
            self.db.query(Expense)
            .outerjoin(Unit, Expense.unit_id == Unit.id)
            .options(
                joinedload(Expense.category),
                joinedload(Expense.building),
                joinedload(Expense.unit),
                joinedload(Expense.recorder),
            )
        )
        role = actor.role.code
        if role == "super_admin":
            return query
        if role == "admin_familial":
            return query

        allowed_buildings = BuildingAccessService.accessible_building_ids(self.db, actor)
        owner_profile_id = BuildingAccessService.get_owner_profile_id(actor)

        if role == "gestionnaire":
            if not allowed_buildings:
                return query.filter(Expense.id.is_(None))
            return query.filter(
                or_(
                    Expense.building_id.in_(allowed_buildings),
                    Unit.building_id.in_(allowed_buildings),
                )
            )

        if role == "proprietaire":
            filters = []
            if allowed_buildings:
                filters.extend(
                    [
                        Expense.building_id.in_(allowed_buildings),
                        Unit.building_id.in_(allowed_buildings),
                    ]
                )
            if owner_profile_id:
                filters.append(Expense.owner_profile_id == owner_profile_id)
            if not filters:
                return query.filter(Expense.id.is_(None))
            return query.filter(or_(*filters))

        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès non autorisé")

    def _resolve_links(self, payload: ExpenseCreate) -> tuple[UUID | None, UUID | None, UUID | None]:
        building_id = UUID(payload.building_id) if payload.building_id else None
        unit_id = UUID(payload.unit_id) if payload.unit_id else None
        owner_profile_id = UUID(payload.owner_profile_id) if payload.owner_profile_id else None

        if unit_id:
            unit = self.db.query(Unit).filter(Unit.id == unit_id).first()
            if unit is None:
                raise HTTPException(status_code=404, detail="Logement introuvable")
            building_id = unit.building_id

        if not any((building_id, unit_id, owner_profile_id)):
            raise HTTPException(
                status_code=400,
                detail="Au moins un lien immeuble, logement ou propriétaire est requis",
            )
        return building_id, unit_id, owner_profile_id

    def _ensure_link_access(
        self,
        actor: User,
        building_id: UUID | None,
        unit_id: UUID | None,
        owner_profile_id: UUID | None,
    ) -> None:
        if building_id:
            BuildingAccessService.ensure_building_access(self.db, actor, building_id)
        elif unit_id:
            unit = self.db.query(Unit).filter(Unit.id == unit_id).first()
            if unit:
                BuildingAccessService.ensure_building_access(self.db, actor, unit.building_id)
        elif actor.role.code == "gestionnaire":
            raise HTTPException(
                status_code=400,
                detail="Le gestionnaire doit lier la dépense à un immeuble assigné",
            )

    def _ensure_expense_access(self, actor: User, expense: Expense) -> None:
        if actor.role.code in ("super_admin", "admin_familial"):
            return
        if actor.role.code == "gestionnaire":
            building_id = expense.building_id
            if expense.unit_id and expense.unit:
                building_id = expense.unit.building_id
            if building_id is None:
                raise HTTPException(status_code=403, detail="Accès non autorisé")
            BuildingAccessService.ensure_building_access(self.db, actor, building_id)
            return
        if actor.role.code == "proprietaire":
            owner_profile_id = BuildingAccessService.get_owner_profile_id(actor)
            allowed = BuildingAccessService.accessible_building_ids(self.db, actor) or set()
            building_id = expense.building_id
            if expense.unit and expense.unit.building_id:
                building_id = expense.unit.building_id
            if building_id and building_id in allowed:
                return
            if owner_profile_id and expense.owner_profile_id == owner_profile_id:
                return
            if building_id and expense.building and expense.building.owner_profile_id == owner_profile_id:
                return
            raise HTTPException(status_code=403, detail="Accès non autorisé")

    def _get_or_404(self, expense_id: UUID) -> Expense:
        expense = (
            self.db.query(Expense)
            .options(
                joinedload(Expense.category),
                joinedload(Expense.building),
                joinedload(Expense.unit),
                joinedload(Expense.recorder),
                joinedload(Expense.validator),
            )
            .filter(Expense.id == expense_id)
            .first()
        )
        if expense is None:
            raise HTTPException(status_code=404, detail="Dépense introuvable")
        return expense

    def _get_category_or_404(self, category_id: UUID) -> ExpenseCategory:
        category = (
            self.db.query(ExpenseCategory)
            .filter(ExpenseCategory.id == category_id, ExpenseCategory.is_active.is_(True))
            .first()
        )
        if category is None:
            raise HTTPException(status_code=404, detail="Catégorie introuvable")
        return category

    def _ensure_read_access(self, actor: User) -> None:
        if role_has_permission(actor.role.code, Permission.EXPENSES_READ):
            return
        raise HTTPException(status_code=403, detail="Accès non autorisé")

    def _ensure_manage_access(self, actor: User) -> None:
        if role_has_permission(actor.role.code, Permission.EXPENSES_MANAGE):
            return
        raise HTTPException(status_code=403, detail="Accès non autorisé")

    def _category_to_response(self, category: ExpenseCategory) -> ExpenseCategoryResponse:
        return ExpenseCategoryResponse(
            id=str(category.id),
            code=category.code,
            label=category.label,
            is_active=category.is_active,
        )

    def _to_summary(self, expense: Expense) -> ExpenseSummaryItem:
        return ExpenseSummaryItem(
            id=str(expense.id),
            category_code=expense.category.code,
            category_label=expense.category.label,
            building_name=expense.building.name if expense.building else None,
            unit_code=expense.unit.code if expense.unit else None,
            supplier_name=expense.supplier_name,
            description=expense.description,
            amount=expense.amount,
            payment_method=expense.payment_method,
            expense_date=expense.expense_date,
            status=expense.status,
            requires_validation=expense.requires_validation,
            recorded_by_name=f"{expense.recorder.first_name} {expense.recorder.last_name}",
            created_at=expense.created_at,
        )

    def _to_detail(self, expense: Expense) -> ExpenseDetail:
        summary = self._to_summary(expense)
        validator_name = None
        if expense.validator:
            validator_name = f"{expense.validator.first_name} {expense.validator.last_name}"
        return ExpenseDetail(
            **summary.model_dump(),
            building_id=str(expense.building_id) if expense.building_id else None,
            unit_id=str(expense.unit_id) if expense.unit_id else None,
            owner_profile_id=str(expense.owner_profile_id) if expense.owner_profile_id else None,
            receipt_url=expense.receipt_url,
            validated_by_name=validator_name,
            validated_at=expense.validated_at,
            updated_at=expense.updated_at,
        )
