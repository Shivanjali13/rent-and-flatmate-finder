import enum
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime, ForeignKey,
    Enum, Boolean, Text, JSON, UniqueConstraint
)
from sqlalchemy.orm import relationship

from app.database import Base


class UserRole(str, enum.Enum):
    tenant = "tenant"
    owner = "owner"
    admin = "admin"


class ListingStatus(str, enum.Enum):
    active = "active"
    filled = "filled"


class InterestStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    declined = "declined"


class ScoreMethod(str, enum.Enum):
    llm = "llm"
    rule_based = "rule_based"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    name = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    listings = relationship("Listing", back_populates="owner", cascade="all, delete-orphan")
    tenant_profile = relationship("TenantProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")


class Listing(Base):
    __tablename__ = "listings"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    location = Column(String, nullable=False, index=True)
    rent = Column(Float, nullable=False)
    available_from = Column(Date, nullable=False)
    room_type = Column(String, nullable=False)          # e.g. single, shared, 1BHK
    furnishing_status = Column(String, nullable=False)   # e.g. furnished, semi, unfurnished
    photos = Column(JSON, default=list)                  # list of image URLs
    description = Column(Text, nullable=True)
    status = Column(Enum(ListingStatus), default=ListingStatus.active, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="listings")


class TenantProfile(Base):
    __tablename__ = "tenant_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    preferred_location = Column(String, nullable=False)
    budget_min = Column(Float, nullable=False)
    budget_max = Column(Float, nullable=False)
    move_in_date = Column(Date, nullable=False)
    notes = Column(Text, nullable=True)  # free-text preferences fed to the LLM prompt
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="tenant_profile")


class CompatibilityScore(Base):
    """
    Cache table: one row per (listing, tenant) pair.
    Computed once, read on every subsequent browse - never recomputed
    unless the listing or tenant profile changes.
    """
    __tablename__ = "compatibility_scores"
    __table_args__ = (UniqueConstraint("listing_id", "tenant_id", name="uq_listing_tenant"),)

    id = Column(Integer, primary_key=True, index=True)
    listing_id = Column(Integer, ForeignKey("listings.id"), nullable=False)
    tenant_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    score = Column(Integer, nullable=False)
    explanation = Column(Text, nullable=False)
    method = Column(Enum(ScoreMethod), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Interest(Base):
    __tablename__ = "interests"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    listing_id = Column(Integer, ForeignKey("listings.id"), nullable=False)
    status = Column(Enum(InterestStatus), default=InterestStatus.pending, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    responded_at = Column(DateTime, nullable=True)


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    interest_id = Column(Integer, ForeignKey("interests.id"), nullable=False, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow)