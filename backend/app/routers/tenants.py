from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import TenantProfile, User, UserRole
from app.schemas import TenantProfileCreate, TenantProfileOut
from app.deps import require_role

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.put("/profile", response_model=TenantProfileOut)
def upsert_profile(
    payload: TenantProfileCreate,
    db: Session = Depends(get_db),
    tenant: User = Depends(require_role(UserRole.tenant)),
):
    """
    PUT (not POST) because a tenant has exactly one profile - this is an
    idempotent create-or-update, which also lets the frontend use one
    call for both 'first time setup' and 'edit preferences'.
    """
    profile = db.query(TenantProfile).filter(TenantProfile.user_id == tenant.id).first()
    if profile:
        for field, value in payload.model_dump().items():
            setattr(profile, field, value)
    else:
        profile = TenantProfile(user_id=tenant.id, **payload.model_dump())
        db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/profile", response_model=TenantProfileOut)
def get_profile(
    db: Session = Depends(get_db),
    tenant: User = Depends(require_role(UserRole.tenant)),
):
    profile = db.query(TenantProfile).filter(TenantProfile.user_id == tenant.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not set up yet")
    return profile