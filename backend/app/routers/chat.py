from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session

from app.database import get_db, SessionLocal
from app.models import Interest, InterestStatus, Listing, Message, User
from app.schemas import MessageOut
from app.deps import get_current_user
from app.security import decode_access_token

router = APIRouter(tags=["chat"])


def _authorize_thread(db: Session, interest_id: int, user_id: int) -> Interest:
    """
    Shared guard for both the REST history endpoint and the WebSocket
    connection: thread must exist, be accepted, and the caller must be
    one of the two participants. Centralizing this avoids the two entry
    points (REST + WS) drifting out of sync on the authorization rule.
    """
    interest = db.query(Interest).filter(Interest.id == interest_id).first()
    if not interest:
        raise HTTPException(status_code=404, detail="Interest thread not found")
    if interest.status != InterestStatus.accepted:
        raise HTTPException(status_code=403, detail="Chat only available once interest is accepted")

    listing = db.query(Listing).filter(Listing.id == interest.listing_id).first()
    if user_id not in (interest.tenant_id, listing.owner_id):
        raise HTTPException(status_code=403, detail="Not part of this chat thread")
    return interest


@router.get("/interests/{interest_id}/messages", response_model=list[MessageOut])
def get_message_history(
    interest_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _authorize_thread(db, interest_id, user.id)
    return (
        db.query(Message)
        .filter(Message.interest_id == interest_id)
        .order_by(Message.sent_at.asc())
        .all()
    )


class ConnectionManager:
    """
    Keeps active WebSocket connections grouped by interest_id (chat room).
    In-memory is fine for a single-process deployment (Railway/Render free
    tier runs one instance); documented as a known limitation for horizontal
    scaling in the README.
    """
    def __init__(self):
        self.rooms: dict[int, list[WebSocket]] = {}

    async def connect(self, interest_id: int, ws: WebSocket):
        await ws.accept()
        self.rooms.setdefault(interest_id, []).append(ws)

    def disconnect(self, interest_id: int, ws: WebSocket):
        if interest_id in self.rooms and ws in self.rooms[interest_id]:
            self.rooms[interest_id].remove(ws)
            if not self.rooms[interest_id]:
                del self.rooms[interest_id]

    async def broadcast(self, interest_id: int, payload: dict):
        for ws in self.rooms.get(interest_id, []):
            await ws.send_json(payload)


manager = ConnectionManager()


@router.websocket("/ws/chat/{interest_id}")
async def chat_websocket(websocket: WebSocket, interest_id: int, token: str = Query(...)):
    # Browsers can't set custom headers on a WebSocket handshake, so the
    # JWT is passed as a query param instead of the Authorization header.
    payload = decode_access_token(token)
    if payload is None:
        await websocket.close(code=4401)
        return
    user_id = int(payload.get("sub"))

    db = SessionLocal()
    try:
        try:
            _authorize_thread(db, interest_id, user_id)
        except HTTPException as exc:
            await websocket.close(code=4403, reason=exc.detail)
            return

        await manager.connect(interest_id, websocket)
        try:
            while True:
                data = await websocket.receive_json()
                content = (data.get("content") or "").strip()
                if not content:
                    continue

                message = Message(interest_id=interest_id, sender_id=user_id, content=content)
                db.add(message)
                db.commit()
                db.refresh(message)

                await manager.broadcast(interest_id, {
                    "id": message.id,
                    "interest_id": interest_id,
                    "sender_id": user_id,
                    "content": content,
                    "sent_at": message.sent_at.isoformat(),
                })
        except WebSocketDisconnect:
            manager.disconnect(interest_id, websocket)
    finally:
        db.close()