from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Listing, ListingStatus, TenantProfile, CompatibilityScore, User, UserRole
from app.schemas import ListingWithScore
from app.deps import require_role
from app.services.llm_scoring import compute_compatibility

router = APIRouter(prefix="/browse", tags=["matching"])


@router.get("", response_model=list[ListingWithScore])
def browse_listings(
    location: Optional[str] = None,
    min_rent: Optional[float] = None,
    max_rent: Optional[float] = None,
    db: Session = Depends(get_db),
    tenant: User = Depends(require_role(UserRole.tenant)),
):
    profile = db.query(TenantProfile).filter(TenantProfile.user_id == tenant.id).first()
    if not profile:
        raise HTTPException(status_code=400, detail="Set up your tenant profile before browsing")

    # Filled listings are excluded at the query level (not just hidden in the
    # frontend) so they can never leak through the API either.
    query = db.query(Listing).filter(Listing.status == ListingStatus.active)
    if location:
        query = query.filter(Listing.location.ilike(f"%{location}%"))
    if min_rent is not None:
        query = query.filter(Listing.rent >= min_rent)
    if max_rent is not None:
        query = query.filter(Listing.rent <= max_rent)

    listings = query.all()

    results: list[ListingWithScore] = []
    for listing in listings:
        cached = (
            db.query(CompatibilityScore)
            .filter(
                CompatibilityScore.listing_id == listing.id,
                CompatibilityScore.tenant_id == tenant.id,
            )
            .first()
        )

        if cached is None:
            # Compute once, persist, never recompute on future requests
            # unless the listing or profile changes (see PATCH /listings
            # and PUT /tenants/profile - those don't currently invalidate
            # the cache; see README for the documented tradeoff).
            score, explanation, method = compute_compatibility(profile, listing)
            cached = CompatibilityScore(
                listing_id=listing.id,
                tenant_id=tenant.id,
                score=score,
                explanation=explanation,
                method=method,
            )
            db.add(cached)
            db.commit()
            db.refresh(cached)

        item = ListingWithScore.model_validate(listing)
        item.compatibility_score = cached.score
        item.compatibility_explanation = cached.explanation
        item.score_method = cached.method
        results.append(item)

    results.sort(key=lambda r: r.compatibility_score or 0, reverse=True)
    return results