import json
import logging
from datetime import date

import httpx

from app.config import settings
from app.models import Listing, TenantProfile

logger = logging.getLogger("llm_scoring")

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

SYSTEM_PROMPT = (
    "You are a rental-matching assistant. Given a tenant's preferences and a room "
    "listing, evaluate how compatible they are. Respond with ONLY valid JSON, no "
    'markdown, no extra text, in this exact shape: {"score": <integer 0-100>, '
    '"explanation": "<one concise sentence>"}. Score higher when location matches '
    "closely, rent fits within budget, and move-in date aligns with availability."
)


def _build_user_prompt(tenant: TenantProfile, listing: Listing) -> str:
    return (
        f"Tenant preferences: preferred_location={tenant.preferred_location}, "
        f"budget=₹{tenant.budget_min:.0f}-₹{tenant.budget_max:.0f}, "
        f"move_in_date={tenant.move_in_date}, notes={tenant.notes or 'none'}\n"
        f"Listing: location={listing.location}, rent=₹{listing.rent:.0f}, "
        f"available_from={listing.available_from}, room_type={listing.room_type}, "
        f"furnishing={listing.furnishing_status}"
    )


def _rule_based_score(tenant: TenantProfile, listing: Listing) -> tuple[int, str]:
    """
    Deterministic fallback used when the LLM is unavailable or returns
    something unparseable. Mirrors the same signals the LLM prompt asks
    about so scores stay roughly comparable across methods.
    """
    score = 0
    reasons = []

    # Location match (simple case-insensitive substring check)
    t_loc = tenant.preferred_location.strip().lower()
    l_loc = listing.location.strip().lower()
    if t_loc == l_loc:
        score += 50
        reasons.append("location matches exactly")
    elif t_loc in l_loc or l_loc in t_loc:
        score += 35
        reasons.append("location partially matches")
    else:
        reasons.append("location does not match")

    # Budget fit
    if tenant.budget_min <= listing.rent <= tenant.budget_max:
        score += 30
        reasons.append("rent is within budget")
    elif listing.rent <= tenant.budget_max * 1.15:
        score += 15
        reasons.append("rent is slightly above budget")
    else:
        reasons.append("rent is well above budget")

    # Move-in date proximity (within 14 days = full points)
    delta_days = abs((listing.available_from - tenant.move_in_date).days)
    if delta_days <= 14:
        score += 20
        reasons.append("availability aligns with move-in date")
    elif delta_days <= 45:
        score += 10
        reasons.append("availability is somewhat close to move-in date")
    else:
        reasons.append("availability is far from move-in date")

    score = max(0, min(100, score))
    explanation = "Rule-based match: " + "; ".join(reasons) + "."
    return score, explanation


def _call_llm(tenant: TenantProfile, listing: Listing) -> tuple[int, str]:
    """
    Raises on any failure (network, timeout, bad response, bad JSON) so the
    caller can catch and fall back. Keeping this function 'fail loud' makes
    the fallback path explicit rather than silently swallowed inside here.
    """
    if not settings.GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY not configured")

    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    body = {
        "model": settings.GROQ_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_prompt(tenant, listing)},
        ],
        "temperature": 0.3,
        "max_tokens": 200,
    }

    with httpx.Client(timeout=settings.LLM_TIMEOUT_SECONDS) as client:
        resp = client.post(GROQ_URL, headers=headers, json=body)
        resp.raise_for_status()
        data = resp.json()

    raw_text = data["choices"][0]["message"]["content"].strip()
    # Strip accidental markdown code fences if the model adds them anyway
    raw_text = raw_text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    parsed = json.loads(raw_text)
    score = int(parsed["score"])
    explanation = str(parsed["explanation"])[:500]

    if not (0 <= score <= 100):
        raise ValueError(f"LLM returned out-of-range score: {score}")

    return score, explanation


def compute_compatibility(tenant: TenantProfile, listing: Listing) -> tuple[int, str, str]:
    """
    Returns (score, explanation, method). Tries the LLM first; on ANY
    failure (timeout, API error, malformed JSON, out-of-range score) falls
    back to the deterministic rule-based scorer so the user always gets a
    result instead of a broken request.
    """
    try:
        score, explanation = _call_llm(tenant, listing)
        return score, explanation, "llm"
    except Exception as exc:
        logger.warning("LLM scoring failed, using rule-based fallback: %s", exc)
        score, explanation = _rule_based_score(tenant, listing)
        return score, explanation, "rule_based"