"""Private direct messages. Conversations require an accepted friendship or mutual event networking opt-in."""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, or_, and_, func
from sqlalchemy.orm import Session
from auth import get_current_user
from database import get_db
from models import User, FriendRequest, EventAttendance, PublicProfile, DirectConversation, DirectMessage
from routers.community import blocked

router = APIRouter(prefix='/messages', tags=['messaging'])

class StartConversation(BaseModel):
    recipient_id: int

class SendMessage(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


def allowed_to_connect(db: Session, a: int, b: int) -> bool:
    if a == b or not db.get(User, b) or blocked(db, a, b):
        return False
    friends = db.scalar(select(FriendRequest.id).where(
        FriendRequest.status == 'accepted',
        or_(and_(FriendRequest.sender_id == a, FriendRequest.receiver_id == b),
            and_(FriendRequest.sender_id == b, FriendRequest.receiver_id == a))))
    if friends is not None:
        return True
    # Both participants must explicitly opt into networking at the same event.
    p1, p2 = db.get(PublicProfile, a), db.get(PublicProfile, b)
    if not p1 or not p2 or not p1.discoverable or not p2.discoverable:
        return False
    a_events = select(EventAttendance.event_id).where(EventAttendance.user_id == a,
        EventAttendance.visible.is_(True), EventAttendance.networking.is_(True))
    return db.scalar(select(EventAttendance.id).where(EventAttendance.user_id == b,
        EventAttendance.visible.is_(True), EventAttendance.networking.is_(True),
        EventAttendance.event_id.in_(a_events)).limit(1)) is not None


def participant(db: Session, conversation_id: int, user_id: int) -> DirectConversation:
    c = db.get(DirectConversation, conversation_id)
    if not c or user_id not in (c.user_low_id, c.user_high_id):
        raise HTTPException(404, 'Conversation not found')
    other = c.user_high_id if c.user_low_id == user_id else c.user_low_id
    if blocked(db, user_id, other):
        raise HTTPException(403, 'Conversation unavailable')
    return c


def conversation_data(c: DirectConversation, me: int) -> dict:
    return {'id': c.id, 'other_user_id': c.user_high_id if c.user_low_id == me else c.user_low_id,
            'created_at': c.created_at.isoformat() + 'Z'}

@router.post('/conversations', status_code=201)
def start(body: StartConversation, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not allowed_to_connect(db, user.id, body.recipient_id):
        raise HTTPException(403, 'You must be friends or mutually opted in to the same event networking')
    low, high = sorted((user.id, body.recipient_id))
    c = db.scalar(select(DirectConversation).where(DirectConversation.user_low_id == low,
                                                    DirectConversation.user_high_id == high))
    if c is None:
        c = DirectConversation(user_low_id=low, user_high_id=high)
        db.add(c)
        db.commit()
        db.refresh(c)
    return conversation_data(c, user.id)

@router.get('/conversations')
def list_conversations(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(DirectConversation).where(or_(DirectConversation.user_low_id == user.id,
        DirectConversation.user_high_id == user.id)).order_by(DirectConversation.id.desc())).all()
    return [conversation_data(c, user.id) for c in rows if not blocked(db, user.id,
        c.user_high_id if c.user_low_id == user.id else c.user_low_id)]

@router.get('/conversations/{conversation_id}')
def get_messages(conversation_id: int, limit: int = Query(50, ge=1, le=100),
                 before_id: int | None = Query(None, ge=1), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    participant(db, conversation_id, user.id)
    stmt = select(DirectMessage).where(DirectMessage.conversation_id == conversation_id)
    if before_id:
        stmt = stmt.where(DirectMessage.id < before_id)
    messages = db.scalars(stmt.order_by(DirectMessage.id.desc()).limit(limit)).all()
    return [{'id': m.id, 'sender_id': m.sender_id, 'text': m.text,
             'created_at': m.created_at.isoformat() + 'Z'} for m in reversed(messages)]

@router.post('/conversations/{conversation_id}', status_code=201)
def send_message(conversation_id: int, body: SendMessage, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    c = participant(db, conversation_id, user.id)
    other = c.user_high_id if c.user_low_id == user.id else c.user_low_id
    if not allowed_to_connect(db, user.id, other):
        raise HTTPException(403, 'Connection is no longer permitted')
    message = DirectMessage(conversation_id=c.id, sender_id=user.id, text=body.text.strip())
    if not message.text:
        raise HTTPException(422, 'Message cannot be blank')
    db.add(message)
    db.commit()
    db.refresh(message)
    return {'id': message.id, 'conversation_id': c.id, 'sender_id': user.id,
            'text': message.text, 'created_at': message.created_at.isoformat() + 'Z'}
