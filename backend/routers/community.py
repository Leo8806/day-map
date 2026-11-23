"""Event attendance and opt-in networking. No private contact details are exposed."""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session
from auth import get_current_user
from database import get_db
from models import User, Event, EventAttendance, PublicProfile, UserBlock

router = APIRouter(tags=['community'])

class RSVPInput(BaseModel):
    visible: bool = False
    networking: bool = False

class ProfileInput(BaseModel):
    major: str = Field(default='', max_length=120)
    graduation_year: int | None = Field(default=None, ge=2020, le=2100)
    bio: str = Field(default='', max_length=500)
    interests: str = Field(default='', max_length=500)
    discoverable: bool = False

def public_profile(db, user_id):
    user = db.get(User, user_id)
    profile = db.get(PublicProfile, user_id)
    return {'id': user.id, 'name': user.name, 'major': profile.major if profile else '',
            'graduation_year': profile.graduation_year if profile else None,
            'bio': profile.bio if profile else '', 'interests': profile.interests if profile else ''}

def blocked(db, a, b):
    return db.scalar(select(UserBlock.id).where(or_(
        (UserBlock.blocker_id == a) & (UserBlock.blocked_id == b),
        (UserBlock.blocker_id == b) & (UserBlock.blocked_id == a)))) is not None

@router.put('/users/me/public-profile')
def update_profile(payload: ProfileInput, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.get(PublicProfile, user.id)
    if not profile:
        profile = PublicProfile(user_id=user.id)
        db.add(profile)
    for field, value in payload.model_dump().items():
        setattr(profile, field, value)
    db.commit()
    return {**public_profile(db, user.id), 'discoverable': profile.discoverable}

@router.get('/users/{user_id}/public-profile')
def get_profile(user_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    target = db.get(User, user_id)
    if not target or blocked(db, user.id, user_id):
        raise HTTPException(404, 'Profile not available')
    profile = db.get(PublicProfile, user_id)
    if user.id != user_id and (not profile or not profile.discoverable):
        raise HTTPException(404, 'Profile not available')
    return public_profile(db, user_id)

@router.put('/events/{event_id}/rsvp')
def rsvp(event_id: int, payload: RSVPInput, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    event = db.get(Event, event_id)
    if not event or event.status != 'approved':
        raise HTTPException(404, 'Event not found')
    if payload.networking and not payload.visible:
        raise HTTPException(422, 'Networking requires visible attendance')
    if payload.networking:
        profile = db.get(PublicProfile, user.id)
        if not profile or not profile.discoverable:
            raise HTTPException(422, 'Enable public profile discovery before networking')
    record = db.scalar(select(EventAttendance).where(EventAttendance.event_id == event_id, EventAttendance.user_id == user.id))
    if not record:
        record = EventAttendance(event_id=event_id, user_id=user.id)
        db.add(record)
    record.visible = payload.visible
    record.networking = payload.networking
    db.commit()
    return {'event_id': event_id, 'going': True, 'visible': record.visible, 'networking': record.networking}

@router.delete('/events/{event_id}/rsvp')
def cancel_rsvp(event_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    record = db.scalar(select(EventAttendance).where(EventAttendance.event_id == event_id, EventAttendance.user_id == user.id))
    if not record:
        raise HTTPException(404, 'RSVP not found')
    db.delete(record)
    db.commit()
    return {'going': False}

@router.get('/events/{event_id}/attendees')
def attendees(event_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    event = db.get(Event, event_id)
    if not event or event.status != 'approved':
        raise HTTPException(404, 'Event not found')
    count = db.scalar(select(func.count()).select_from(EventAttendance).where(EventAttendance.event_id == event_id))
    records = db.scalars(select(EventAttendance).where(EventAttendance.event_id == event_id, EventAttendance.visible.is_(True))).all()
    people = [public_profile(db, r.user_id) for r in records if not blocked(db, user.id, r.user_id) and
              (r.user_id == user.id or (db.get(PublicProfile, r.user_id) and db.get(PublicProfile, r.user_id).discoverable))]
    return {'event_id': event_id, 'going_count': count, 'visible_attendees': people}

@router.get('/events/{event_id}/networking')
def networking(event_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    event = db.get(Event, event_id)
    if not event or event.status != 'approved':
        raise HTTPException(404, 'Event not found')
    own = db.scalar(select(EventAttendance).where(EventAttendance.event_id == event_id, EventAttendance.user_id == user.id))
    if not own or not own.networking:
        raise HTTPException(403, 'Opt in to event networking to see other participants')
    records = db.scalars(select(EventAttendance).where(EventAttendance.event_id == event_id, EventAttendance.networking.is_(True), EventAttendance.visible.is_(True))).all()
    return {'attendees': [public_profile(db, r.user_id) for r in records if r.user_id != user.id and
                          not blocked(db, user.id, r.user_id) and
                          (db.get(PublicProfile, r.user_id) and db.get(PublicProfile, r.user_id).discoverable)]}

@router.post('/users/{user_id}/block')
def block_user(user_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user_id == user.id or not db.get(User, user_id):
        raise HTTPException(400, 'Invalid user')
    if not db.scalar(select(UserBlock).where(UserBlock.blocker_id == user.id, UserBlock.blocked_id == user_id)):
        db.add(UserBlock(blocker_id=user.id, blocked_id=user_id))
        db.commit()
    return {'blocked': True}

@router.delete('/users/{user_id}/block')
def unblock_user(user_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    record = db.scalar(select(UserBlock).where(UserBlock.blocker_id == user.id, UserBlock.blocked_id == user_id))
    if record:
        db.delete(record)
        db.commit()
    return {'blocked': False}
