from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.owner_profile import OwnerProfile
from app.schemas.owner_profile import (
    OwnerProfileCreate,
    OwnerProfileListResponse,
    OwnerProfileResponse,
    OwnerProfileUpdate,
)


class OwnerProfileService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_profiles(self) -> OwnerProfileListResponse:
        profiles = self.db.query(OwnerProfile).order_by(OwnerProfile.created_at.desc()).all()
        return OwnerProfileListResponse(items=[self._to_response(item) for item in profiles])

    def create_profile(self, payload: OwnerProfileCreate) -> OwnerProfileResponse:
        profile = OwnerProfile(
            first_name=payload.first_name.strip(),
            last_name=payload.last_name.strip(),
            phone=payload.phone,
            email=payload.email.strip().lower() if payload.email else None,
            notes=payload.notes,
        )
        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)
        return self._to_response(profile)

    def update_profile(
        self, profile_id: UUID, payload: OwnerProfileUpdate
    ) -> OwnerProfileResponse:
        profile = self._get_or_404(profile_id)
        if payload.first_name is not None:
            profile.first_name = payload.first_name.strip()
        if payload.last_name is not None:
            profile.last_name = payload.last_name.strip()
        if payload.phone is not None:
            profile.phone = payload.phone
        if payload.email is not None:
            profile.email = payload.email.strip().lower() if payload.email else None
        if payload.notes is not None:
            profile.notes = payload.notes
        self.db.commit()
        self.db.refresh(profile)
        return self._to_response(profile)

    def _get_or_404(self, profile_id: UUID) -> OwnerProfile:
        profile = self.db.query(OwnerProfile).filter(OwnerProfile.id == profile_id).first()
        if profile is None:
            raise HTTPException(status_code=404, detail="Profil propriétaire introuvable")
        return profile

    def _to_response(self, profile: OwnerProfile) -> OwnerProfileResponse:
        return OwnerProfileResponse(
            id=str(profile.id),
            first_name=profile.first_name,
            last_name=profile.last_name,
            phone=profile.phone,
            email=profile.email,
            notes=profile.notes,
            user_id=str(profile.user_id) if profile.user_id else None,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )
