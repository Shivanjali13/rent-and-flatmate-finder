from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.config import settings
from app.routers import auth, listings, tenants, matching, interests, chat, admin

# Day-1 scope: create tables directly instead of Alembic migrations.
# Trade-off documented in README - saves setup time on a 2-day build;
# swap for Alembic if this project continues past the deadline.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Rent & Flatmate Finder API")

origins = [o.strip() for o in settings.FRONTEND_ORIGIN.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(listings.router)
app.include_router(tenants.router)
app.include_router(matching.router)
app.include_router(interests.router)
app.include_router(chat.router)
app.include_router(admin.router)


@app.get("/health")
def health():
    return {"status": "ok"}