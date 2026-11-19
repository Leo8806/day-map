from datetime import timezone

from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import Base, engine, get_db
from models import User, Event
from schemas import (
    UserCreate,
    UserResponse,
    UserLogin,
    UserUpdate,
    TokenResponse,
    EventCreate,
    EventResponse,
)
from auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    get_current_admin,
)


# --------------------------------------------------
# Initialize FastAPI and Database
# --------------------------------------------------

app = FastAPI(title="Day Map API")

Base.metadata.create_all(bind=engine)


# --------------------------------------------------
# General Endpoints
# --------------------------------------------------

@app.get("/")
def home():
    return {"message": "Welcome to Day Map!"}


@app.get("/health")
def health():
    return {"status": "running"}


# --------------------------------------------------
# Authentication
# --------------------------------------------------

@app.post(
    "/auth/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    email = str(user_data.email).lower()

    existing_user = db.scalar(
        select(User).where(User.email == email)
    )

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Email already registered"
        )

    new_user = User(
        name=user_data.name,
        email=email,
        password_hash=hash_password(user_data.password),
        is_admin=False,
        interests=""
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@app.post(
    "/auth/login",
    response_model=TokenResponse
)
def login(
    credentials: UserLogin,
    db: Session = Depends(get_db)
):
    email = str(credentials.email).lower()

    user = db.scalar(
        select(User).where(User.email == email)
    )

    if not user or not verify_password(
        credentials.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    token = create_access_token(user.id)

    return {
        "access_token": token,
        "token_type": "bearer"
    }


# --------------------------------------------------
# User Profiles
# --------------------------------------------------

@app.get(
    "/users/me",
    response_model=UserResponse
)
def get_my_profile(
    current_user: User = Depends(get_current_user)
):
    return current_user


@app.patch(
    "/users/me",
    response_model=UserResponse
)
def update_my_profile(
    updates: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if updates.name is not None:
        current_user.name = updates.name

    if updates.interests is not None:
        current_user.interests = updates.interests

    db.commit()
    db.refresh(current_user)

    return current_user


# --------------------------------------------------
# Event Submission
# --------------------------------------------------

@app.post(
    "/events",
    response_model=EventResponse,
    status_code=status.HTTP_201_CREATED
)
def create_event(
    event_data: EventCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    new_event = Event(
        title=event_data.title,
        description=event_data.description,
        location=event_data.location,
        start_time=event_data.start_time.astimezone(
            timezone.utc
        ).replace(tzinfo=None),
        end_time=event_data.end_time.astimezone(
            timezone.utc
        ).replace(tzinfo=None),
        category=event_data.category,
        created_by=current_user.id,
        status="pending"
    )

    db.add(new_event)
    db.commit()
    db.refresh(new_event)

    return new_event


# --------------------------------------------------
# Public Events
# --------------------------------------------------

@app.get(
    "/events",
    response_model=list[EventResponse]
)
def get_approved_events(
    db: Session = Depends(get_db)
):
    events = db.scalars(
        select(Event)
        .where(Event.status == "approved")
        .order_by(Event.start_time)
    ).all()

    return events


# --------------------------------------------------
# Administrator Endpoints
# --------------------------------------------------

@app.get(
    "/admin/events/pending",
    response_model=list[EventResponse]
)
def get_pending_events(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    events = db.scalars(
        select(Event)
        .where(Event.status == "pending")
        .order_by(Event.start_time)
    ).all()

    return events


@app.patch(
    "/admin/events/{event_id}/approve",
    response_model=EventResponse
)
def approve_event(
    event_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    event = db.get(Event, event_id)

    if event is None:
        raise HTTPException(
            status_code=404,
            detail="Event not found"
        )

    if event.status != "pending":
        raise HTTPException(
            status_code=409,
            detail="Only pending events can be approved"
        )

    event.status = "approved"

    db.commit()
    db.refresh(event)

    return event


@app.patch(
    "/admin/events/{event_id}/reject",
    response_model=EventResponse
)
def reject_event(
    event_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    event = db.get(Event, event_id)

    if event is None:
        raise HTTPException(
            status_code=404,
            detail="Event not found"
        )

    if event.status != "pending":
        raise HTTPException(
            status_code=409,
            detail="Only pending events can be rejected"
        )

    event.status = "rejected"

    db.commit()
    db.refresh(event)

    return event
