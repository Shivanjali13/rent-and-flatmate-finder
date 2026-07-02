from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import User, UserRole, Listing, ListingStatus, Interest, InterestStatus, Message
from app.schemas import UserOut, ListingOut
from app.deps import require_role

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), admin: User = Depends(require_role(UserRole.admin))):
    return db.query(User).all()


@router.post("/users/{user_id}/deactivate", response_model=UserOut)
def deactivate_user(user_id: int, db: Session = Depends(get_db), admin: User = Depends(require_role(UserRole.admin))):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = False
    db.commit()
    db.refresh(user)
    return user


@router.post("/users/{user_id}/activate", response_model=UserOut)
def activate_user(user_id: int, db: Session = Depends(get_db), admin: User = Depends(require_role(UserRole.admin))):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = True
    db.commit()
    db.refresh(user)
    return user


@router.get("/listings", response_model=list[ListingOut])
def list_all_listings(db: Session = Depends(get_db), admin: User = Depends(require_role(UserRole.admin))):
    return db.query(Listing).all()


@router.delete("/listings/{listing_id}", status_code=204)
def delete_listing(listing_id: int, db: Session = Depends(get_db), admin: User = Depends(require_role(UserRole.admin))):
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    db.delete(listing)
    db.commit()


@router.get("/stats")
def platform_stats(db: Session = Depends(get_db), admin: User = Depends(require_role(UserRole.admin))):
    users_by_role = dict(
        db.query(User.role, func.count(User.id)).group_by(User.role).all()
    )
    listings_by_status = dict(
        db.query(Listing.status, func.count(Listing.id)).group_by(Listing.status).all()
    )
    interests_by_status = dict(
        db.query(Interest.status, func.count(Interest.id)).group_by(Interest.status).all()
    )

    return {
        "total_users": db.query(func.count(User.id)).scalar(),
        "users_by_role": {k.value if hasattr(k, "value") else k: v for k, v in users_by_role.items()},
        "total_listings": db.query(func.count(Listing.id)).scalar(),
        "listings_by_status": {k.value if hasattr(k, "value") else k: v for k, v in listings_by_status.items()},
        "total_interests": db.query(func.count(Interest.id)).scalar(),
        "interests_by_status": {k.value if hasattr(k, "value") else k: v for k, v in interests_by_status.items()},
        "total_messages": db.query(func.count(Message.id)).scalar(),
    }