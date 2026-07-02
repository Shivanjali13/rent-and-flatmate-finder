from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, ConfigDict

from app.models import UserRole, ListingStatus, InterestStatus, ScoreMethod


# ---------- Auth ----------

class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: UserRole


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: EmailStr
    role: UserRole
    is_active: bool


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------- Listings ----------

class ListingCreate(BaseModel):
    location: str
    rent: float
    available_from: date
    room_type: str
    furnishing_status: str
    photos: list[str] = []
    description: Optional[str] = None


class ListingUpdate(BaseModel):
    location: Optional[str] = None
    rent: Optional[float] = None
    available_from: Optional[date] = None
    room_type: Optional[str] = None
    furnishing_status: Optional[str] = None
    photos: Optional[list[str]] = None
    description: Optional[str] = None
    status: Optional[ListingStatus] = None


class ListingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    owner_id: int
    location: str
    rent: float
    available_from: date
    room_type: str
    furnishing_status: str
    photos: list[str]
    description: Optional[str]
    status: ListingStatus
    created_at: datetime


class ListingWithScore(ListingOut):
    compatibility_score: Optional[int] = None
    compatibility_explanation: Optional[str] = None
    score_method: Optional[ScoreMethod] = None


# ---------- Tenant profile ----------

class TenantProfileCreate(BaseModel):
    preferred_location: str
    budget_min: float
    budget_max: float
    move_in_date: date
    notes: Optional[str] = None


class TenantProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    preferred_location: str
    budget_min: float
    budget_max: float
    move_in_date: date
    notes: Optional[str]


# ---------- Interests ----------

class InterestCreate(BaseModel):
    listing_id: int


class InterestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    tenant_id: int
    listing_id: int
    status: InterestStatus
    created_at: datetime
    responded_at: Optional[datetime]


class InterestStatusUpdate(BaseModel):
    status: InterestStatus  # accepted | declined


# ---------- Messages ----------

class MessageCreate(BaseModel):
    content: str


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    interest_id: int
    sender_id: int
    content: str
    sent_at: datetime