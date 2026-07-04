# Rent & Flatmate Finder

It is an AI-powered platform where room owners list rooms and tenants create profiles in order to look for rooms according to their need and budget. An LLM-based compatibility engine scores and ranks matches, real-time
WebSocket chat unlocks once mutual interest is confirmed between the tenant and owner, and email notifications are also used for communication.


Live API: [optimistic-insight-production-d668.up.railway.app](optimistic-insight-production-d668.up.railway.app)
(interactive docs at [optimistic-insight-production-d668.up.railway.app](optimistic-insight-production-d668.up.railway.app>/docs))
---

## Table of Contents

1. [Tech Stack](#tech-stack)
2. [Setup Guide (Local Development)](#setup-guide-local-development)
3. [Environment Variables](#environment-variables)
4. [Database Schema](#database-schema)
5. [API Documentation](#api-documentation)
6. [LLM Compatibility Scoring — Prompt & Example I/O](#llm-compatibility-scoring--prompt--example-io)
7. [Real-Time Chat](#real-time-chat)
8. [Email Notifications](#email-notifications)
9. [Known Limitations](#known-limitations)

---

## Tech Stack

| Layer    | Technology                                  |
|--------------------------------------------------------|
| Backend  | FastAPI (Python 3.12)                       |
| Database | PostgreSQL (SQLAlchemy ORM)                 |
| Frontend | React 18 + Vite                             |
| Auth     | JWT (python-jose) + bcrypt password hashing |
| Real-time chat | Native FastAPI WebSockets             |
| LLM      | Groq API (Llama 3.3 70B)                    |
| Email    | Resend                                      |
| Hosting  | Backend → Railway, Frontend → Vercel        |



---

## Setup Guide (Local Development)

### Prerequisites
- Python version 3.12
- Node.js 18+
- A PostgreSQL database (local, or a free instance from Railway)
- A [Groq API key](https://console.groq.com) (free tier)
- A [Resend API key](https://resend.com) (free tier)

### Backend

Git Bash commands for backend setup

```bash
cd backend
python -m venv venv
source venv/bin/activate        
pip install -r requirements.txt

cp .env.example .env
# Edit .env and fill in DATABASE_URL, JWT_SECRET_KEY, GROQ_API_KEY, RESEND_API_KEY

uvicorn app.main:app --reload
```

The API is now running at `http://127.0.0.1:8000`. Visit `http://127.0.0.1:8000/docs`
for interactive Swagger UI. Tables are created automatically on startup
(`Base.metadata.create_all()` in `app/main.py`) — no manual migration step needed.

### Frontend

git bash commands for frontend setup
```bash
cd frontend
cp .env.example .env
# Edit .env: point VITE_API_URL and VITE_WS_URL at your backend

npm install
npm run dev
```

The app is now running at `http://127.0.0.1:5173`.

### Quick smoke test
Smoke test-> It is a quick check while building a software to verify its stability and key functionalities.

1. Register an **owner** account, log in, post a listing.
2. Register a **tenant** account, log in, set your preference profile.
3. Go to Browse — you should see the listing ranked with an AI compatibility score.
4. Click "Express Interest" → log back in as the owner → accept it.
5. Open Chat from either account and send a message.

---

## Environment Variables

### Backend (`backend/.env`)

| Variable             | Description                                                                          |
|-------------------------------------------------------------------------------------------------------------|
| `DATABASE_URL`       | PostgreSQL connection string, e.g. `postgresql+psycopg://user:pass@host:5432/dbname` |
| `JWT_SECRET_KEY`     | Long random string used to sign JWTs                                                 |
| `JWT_ALGORITHM`      | Default `HS256`                                                                      |
| `JWT_EXPIRE_MINUTES` | Token lifetime in minutes (default `1440` = 24h)                                     |
| `GROQ_API_KEY`       | API key from console.groq.com                                                        |
| `GROQ_MODEL`         | Default `llama-3.3-70b-versatile`                                                    |
| `LLM_TIMEOUT_SECONDS`| Timeout before falling back to rule-based scoring (default `6`)                      |
| `RESEND_API_KEY`     | API key from resend.com                                                              |
| `EMAIL_FROM`         | Sender address (default `onboarding@resend.dev` for testing)                         |
| `HIGH_MATCH_THRESHOLD` | Score above which the owner gets a "strong match" email (default `80`)             |
| `FRONTEND_ORIGIN`    | Comma-separated allowed CORS origins                                                 |

See `backend/.env.example` for the template.

### Frontend (`frontend/.env`)

| Variable        | Description                                                                             |
|-----------------------------------------------------------------------------------------------------------|
| `VITE_API_URL`  | Base URL of the deployed backend, e.g. `https://your-app.up.railway.app`                |
| `VITE_WS_URL`   | WebSocket base URL, same host but `wss://` scheme, e.g. `wss://your-app.up.railway.app` |

See `frontend/.env.example` for the template.

---

## Database Schema

All tables are defined in `backend/app/models.py`.

```
users
├── id                 PK
├── email              unique
├── password_hash
├── name
├── role               enum: tenant | owner | admin
├── is_active          bool
└── created_at

listings
├── id                 PK
├── owner_id           FK -> users.id
├── location
├── rent               float
├── available_from     date
├── room_type          e.g. single, shared, 1BHK
├── furnishing_status  e.g. furnished, semi-furnished, unfurnished
├── photos             JSON list of image URLs
├── description        text, optional
├── status             enum: active | filled
└── created_at

tenant_profiles
├── id                 PK
├── user_id            FK -> users.id, unique (one profile per tenant)
├── preferred_location
├── budget_min         float
├── budget_max         float
├── move_in_date       date
├── notes              text, optional — free-text fed into the LLM prompt
└── created_at

compatibility_scores        -- cache table: computed once per (listing, tenant) pair
├── id                 PK
├── listing_id         FK -> listings.id
├── tenant_id          FK -> users.id
├── score              int, 0-100
├── explanation        text
├── method             enum: llm | rule_based
├── created_at
└── UNIQUE(listing_id, tenant_id)

interests
├── id                 PK
├── tenant_id          FK -> users.id
├── listing_id         FK -> listings.id
├── status             enum: pending | accepted | declined
├── created_at
└── responded_at       nullable

messages
├── id                 PK
├── interest_id        FK -> interests.id
├── sender_id          FK -> users.id
├── content            text
└── sent_at
```

**Key design decision:** `compatibility_scores` is a cache, not a computed-on-the-fly
value. It's written once (on first browse, or on interest creation if the tenant
skipped browsing) and read on every subsequent request — satisfying the requirement
that scores are "stored in DB, not recomputed on every request."

---

## API Documentation

Full interactive docs are auto-generated by FastAPI at `/docs` (Swagger) and `/redoc`.
Summary of all endpoints:

### Auth (`app/routers/auth.py`)
| Method | Path             | Auth | Description                                                      |
|--------|------------------|------|------------------------------------------------------------------|
| POST   | `/auth/register` | none | Register as tenant/owner/admin                                   |
| POST   | `/auth/login`    | none | Returns JWT + user object (form-encoded: `username`, `password`) |

### Listings (`app/routers/listings.py`)
| Method | Path             | Auth  | Description                                            |
|--------|------------------|-------|--------------------------------------------------------|
| POST   | `/listings`      | owner | Create a listing                                       |
| GET    | `/listings/mine` | owner | List your own listings                                 |
| GET    | `/listings/{id}` | any   | Get one listing                                        |
| PATCH  | `/listings/{id}` | owner (must own) | Update fields                               |
| POST   | `/listings/{id}/mark-filled` | owner (must own) | Marks filled, hides from browse |

### Tenant Profile (`app/routers/tenants.py`)
| Method | Path               | Auth   | Description                               |
|--------|--------------------|--------|-------------------------------------------|
| PUT    | `/tenants/profile` | tenant | Create or update preferences (idempotent) |
| GET    | `/tenants/profile` | tenant | Get your own profile                      |

### Matching / Browse (`app/routers/matching.py`)
| Method | Path                                    | Auth   | Description                                 |
|--------|-----------------------------------------|--------|---------------------------------------------|
| GET    | `/browse?location=&min_rent=&max_rent=` | tenant | Filtered, ranked, AI-scored active listings |

### Interests (`app/routers/interests.py`)
| Method | Path              | Auth      | Description                                                                   |
|--------|-------------------|-----------|-------------------------------------------------------------------------------|
| POST   | `/interests`      | tenant    | Express interest in a listing; triggers high-match email if score > threshold |
| GET    | `/interests/sent` | tenant    | Your sent requests, with listing + score details                              |
| GET    | `/interests/received` | owner | Requests on your listings                                                     |
| PATCH  | `/interests/{id}` | owner (must own listing) | Accept/decline; triggers decision email                        |
| GET    | `/interests/{id}` | either party | Single interest detail                                                     |

### Chat (`app/routers/chat.py`)
| Method | Path                        | Auth         | Description                           |
|--------|-----------------------------|--------------|---------------------------------------|
| GET    | `/interests/{id}/messages`  | either party | Message history (only if `accepted`)  |
| WS     | `/ws/chat/{id}?token=<jwt>` | either party | Live chat socket (only if `accepted`) |

### Admin (`app/routers/admin.py`)
| Method | Path                           | Auth  | Description          |
|--------|--------------------------------|-------|----------------------|
| GET    | `/admin/users`                 | admin | List all users       |
| POST   | `/admin/users/{id}/deactivate` | admin | Deactivate a user    |
| POST   | `/admin/users/{id}/activate`   | admin | Reactivate a user    |
| GET    | `/admin/listings`              | admin | List all listings    |
| DELETE | `/admin/listings/{id}`         | admin | Delete a listing     |
| GET    | `/admin/stats`                 | admin | Platform-wide counts |

### Example: Register + Login

```bash
curl -X POST https://your-api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Priya Sharma","email":"priya@example.com","password":"secret123","role":"tenant"}'

curl -X POST https://your-api/auth/login \
  -d "username=priya@example.com&password=secret123"
# → {"access_token": "eyJ...", "token_type": "bearer", "user": {...}}
```

Use the returned `access_token` as `Authorization: Bearer <token>` on all subsequent
requests.

---

## LLM Compatibility Scoring — Prompt & Example I/O

Implemented in `backend/app/services/llm_scoring.py`. Score is computed **once** per
(tenant, listing) pair and cached — see `compatibility_scores` table above.

### System Prompt
```
You are a rental-matching assistant. Given a tenant's preferences and a room
listing, evaluate how compatible they are as per the available options. Respond with ONLY valid JSON, no
markdown, no extra text, in this exact shape: {"score": <integer 0-100>,
"explanation": "<one concise sentence>"}. Score higher when location matches
closely, rent fits within budget, and move-in date aligns with availability.
```

### User Prompt Template
```
Tenant preferences: preferred_location={location}, budget=₹{min}-₹{max},
move_in_date={date}, notes={notes}
Listing: location={location}, rent=₹{rent}, available_from={date},
room_type={type}, furnishing={status}
```

### Example Input
```
Tenant preferences: preferred_location=Kanpur Nagar, budget=₹6000-₹9000,
move_in_date=2026-07-20, notes=Quiet flatmate preferred, non-smoker
Listing: location=Kanpur Nagar, rent=₹8000, available_from=2026-07-15,
room_type=single, furnishing=furnished
```

### Example Output
```json
{
  "score": 92,
  "explanation": "Location matches exactly, rent is comfortably within budget, and the room is available just before the desired move-in date."
}
```

### Fallback: Rule-Based Scoring

If the Groq API times out, errors, or returns malformed/out-of-range JSON, the system
falls back to a deterministic scorer (`_rule_based_score()` in the same file) so the
user always gets a result and there is no downtime for the platform:

| Signal                     | Points  |
|----------------------------|---------|
| Location exact match       | +50     |
| Location partial match     | +35     |
| Rent within budget         | +30     |
| Rent up to 15% over budget | +15     |
| Move-in within 14 days of availability | +20 |
| Move-in within 45 days of availability | +10 |

The `compatibility_scores.method` column records whether a given score came from
`llm` or `rule_based`, and the frontend visibly tags rule-based scores as
"(rule-based estimate)" so the user knows the source of result whether it is llm based or rule based.

---

## Real-Time Chat

- Chat is only reachable once an `Interest` row has `status = accepted` — enforced
  identically in both the REST history endpoint and the WebSocket handshake
  (`_authorize_thread()` in `chat.py`), so there's a single source of truth for the rule.
- The browser WebSocket API can't set custom headers, so the JWT is passed as a query
  parameter: `wss://your-api/ws/chat/{interest_id}?token=<jwt>`.
- Every message is persisted to the `messages` table immediately on receipt, then
  broadcast to both connected participants — refreshing the page reloads full history
  via `GET /interests/{id}/messages`.
- Connections are held in an in-memory `ConnectionManager` keyed by `interest_id`.
  This works well for a single backend instance (Railway free tier runs one); if this
  project were scaled horizontally, that state would need to move to Redis pub/sub.

---

## Email Notifications

Implemented in `backend/app/services/email.py` using Resend.

| Trigger             | Recipient | When                                                                               |
|---------------------|-----------|------------------------------------------------------------------------------------|
| High-match interest | Owner     | Tenant expresses interest with compatibility score > `THRESHOLD` (default 80)      |
| Interest accepted   | Tenant    | Owner accepts the request                                                          |
| Interest declined   | Tenant    | Owner declines the request                                                         |

Email sending is wrapped in try/except — if Resend is down or misconfigured, the
underlying action (creating the interest, accepting/declining) still succeeds; the
failure is only logged, never surfaced as a broken request to the user.

---

