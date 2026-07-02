from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.models import (
    Interest, InterestStatus, Listing, ListingStatus, User, UserRole,
    TenantProfile, CompatibilityScore,
)
from app.schemas import InterestCreate, InterestOut, InterestStatusUpdate, InterestDetailOut
from app.deps import require_role, get_current_user
from app.services.llm_scoring import compute_compatibility
from app.services.email import send_high_match_email, send_interest_decision_email

router = APIRouter(prefix="/interests", tags=["interests"])


@router.post("", response_model=InterestOut, status_code=201)
def create_interest(
    payload: InterestCreate,
    db: Session = Depends(get_db),
    tenant: User = Depends(require_role(UserRole.tenant)),
):
    listing = db.query(Listing).filter(Listing.id == payload.listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if listing.status != ListingStatus.active:
        raise HTTPException(status_code=400, detail="Listing is no longer active")

    existing = (
        db.query(Interest)
        .filter(
            Interest.tenant_id == tenant.id,
            Interest.listing_id == listing.id,
            Interest.status.in_([InterestStatus.pending, InterestStatus.accepted]),
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="You already expressed interest in this listing")

    interest = Interest(tenant_id=tenant.id, listing_id=listing.id, status=InterestStatus.pending)
    db.add(interest)
    db.commit()
    db.refresh(interest)

    # Use the cached score if it exists (tenant likely already browsed this
    # listing); compute it now if not, so the high-match email is never
    # skipped just because they interested directly without browsing first.
    cached = (
        db.query(CompatibilityScore)
        .filter(CompatibilityScore.listing_id == listing.id, CompatibilityScore.tenant_id == tenant.id)
        .first()
    )
    if cached is None:
        profile = db.query(TenantProfile).filter(TenantProfile.user_id == tenant.id).first()
        if profile:
            score, explanation, method = compute_compatibility(profile, listing)
            cached = CompatibilityScore(
                listing_id=listing.id, tenant_id=tenant.id,
                score=score, explanation=explanation, method=method,
            )
            db.add(cached)
            db.commit()
            db.refresh(cached)

    if cached and cached.score > settings.HIGH_MATCH_THRESHOLD:
        owner = db.query(User).filter(User.id == listing.owner_id).first()
        send_high_match_email(
            owner_email=owner.email, owner_name=owner.name, tenant_name=tenant.name,
            listing_location=listing.location, score=cached.score, explanation=cached.explanation,
        )

    return interest


def _to_detail(db: Session, interest: Interest, viewer_role: UserRole) -> InterestDetailOut:
    listing = db.query(Listing).filter(Listing.id == interest.listing_id).first()
    tenant = db.query(User).filter(User.id == interest.tenant_id).first()
    owner = db.query(User).filter(User.id == listing.owner_id).first()
    other = owner if viewer_role == UserRole.tenant else tenant

    score_row = (
        db.query(CompatibilityScore)
        .filter(CompatibilityScore.listing_id == listing.id, CompatibilityScore.tenant_id == tenant.id)
        .first()
    )

    return InterestDetailOut(
        id=interest.id,
        tenant_id=interest.tenant_id,
        listing_id=interest.listing_id,
        status=interest.status,
        created_at=interest.created_at,
        responded_at=interest.responded_at,
        listing_location=listing.location,
        listing_rent=listing.rent,
        listing_room_type=listing.room_type,
        other_party_id=other.id,
        other_party_name=other.name,
        other_party_email=other.email,
        compatibility_score=score_row.score if score_row else None,
        compatibility_explanation=score_row.explanation if score_row else None,
    )


@router.get("/sent", response_model=list[InterestDetailOut])
def sent_interests(
    db: Session = Depends(get_db),
    tenant: User = Depends(require_role(UserRole.tenant)),
):
    interests = db.query(Interest).filter(Interest.tenant_id == tenant.id).order_by(Interest.created_at.desc()).all()
    return [_to_detail(db, i, UserRole.tenant) for i in interests]


@router.get("/received", response_model=list[InterestDetailOut])
def received_interests(
    db: Session = Depends(get_db),
    owner: User = Depends(require_role(UserRole.owner)),
):
    interests = (
        db.query(Interest)
        .join(Listing, Listing.id == Interest.listing_id)
        .filter(Listing.owner_id == owner.id)
        .order_by(Interest.created_at.desc())
        .all()
    )
    return [_to_detail(db, i, UserRole.owner) for i in interests]


@router.patch("/{interest_id}", response_model=InterestOut)
def update_interest_status(
    interest_id: int,
    payload: InterestStatusUpdate,
    db: Session = Depends(get_db),
    owner: User = Depends(require_role(UserRole.owner)),
):
    from datetime import datetime

    interest = db.query(Interest).filter(Interest.id == interest_id).first()
    if not interest:
        raise HTTPException(status_code=404, detail="Interest not found")

    listing = db.query(Listing).filter(Listing.id == interest.listing_id).first()
    if listing.owner_id != owner.id:
        raise HTTPException(status_code=403, detail="Not your listing")

    if payload.status not in (InterestStatus.accepted, InterestStatus.declined):
        raise HTTPException(status_code=400, detail="Status must be 'accepted' or 'declined'")

    interest.status = payload.status
    interest.responded_at = datetime.utcnow()
    db.commit()
    db.refresh(interest)

    tenant = db.query(User).filter(User.id == interest.tenant_id).first()
    send_interest_decision_email(
        tenant_email=tenant.email, tenant_name=tenant.name,
        listing_location=listing.location, status=payload.status.value,
    )

    return interest


@router.get("/{interest_id}", response_model=InterestDetailOut)
def get_interest(
    interest_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    interest = db.query(Interest).filter(Interest.id == interest_id).first()
    if not interest:
        raise HTTPException(status_code=404, detail="Interest not found")

    listing = db.query(Listing).filter(Listing.id == interest.listing_id).first()
    if user.id not in (interest.tenant_id, listing.owner_id) and user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Not part of this interest thread")

    viewer_role = UserRole.tenant if user.id == interest.tenant_id else UserRole.owner
    return _to_detail(db, interest, viewer_role)