import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from database import Base, engine, get_db
from models import User, Event, SavedEvent
from schemas import (
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
    TokenResponse,
    EventCreate,
    EventResponse,
)
from auth import (
    create_access_token,
    get_current_user,
    get_current_admin,
)
from services.scheduler import start_scheduler, stop_scheduler

from pwdlib import PasswordHash


# --------------------------------------------------
# Database Setup
# --------------------------------------------------

Base.metadata.create_all(bind=engine)

password_hash = PasswordHash.recommended()


# --------------------------------------------------
# Scheduler
# --------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    if os.getenv("DAYMAP_ENABLE_SCHEDULER") == "1":
        start_scheduler()

    yield

    if os.getenv("DAYMAP_ENABLE_SCHEDULER") == "1":
        stop_scheduler()


# --------------------------------------------------
# FastAPI Application
# --------------------------------------------------

app = FastAPI(
    title="Day Map API",
    description="Backend API for the Day Map campus event planner",
    version="1.0.0",
    lifespan=lifespan,
)


# --------------------------------------------------
# Helpers
# --------------------------------------------------

def to_utc_naive(dt: datetime) -> datetime:
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


# --------------------------------------------------
# Health
# --------------------------------------------------

@app.get("/")
def root():
    return {"message": "Welcome to Day Map API"}


@app.get("/health")
def health():
    return {"status": "ok"}


# --------------------------------------------------
# Authentication
# --------------------------------------------------

@app.post(
    "/auth/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    user_data: UserCreate,
    db: Session = Depends(get_db),
):
    existing_user = db.scalar(
        select(User).where(User.email == user_data.email)
    )

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered",
        )

    user = User(
        name=user_data.name,
        email=user_data.email,
        password_hash=password_hash.hash(user_data.password),
        is_admin=False,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@app.post("/auth/login", response_model=TokenResponse)
def login(
    credentials: UserLogin,
    db: Session = Depends(get_db),
):
    user = db.scalar(
        select(User).where(User.email == credentials.email)
    )

    if not user or not password_hash.verify(
        credentials.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    token = create_access_token({"sub": str(user.id)})

    return {
        "access_token": token,
        "token_type": "bearer",
    }


# --------------------------------------------------
# User Profile
# --------------------------------------------------

@app.get("/users/me", response_model=UserResponse)
def get_my_profile(
    current_user: User = Depends(get_current_user),
):
    return current_user


@app.patch("/users/me", response_model=UserResponse)
def update_my_profile(
    updates: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    update_data = updates.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(current_user, field, value)

    db.commit()
    db.refresh(current_user)

    return current_user


# --------------------------------------------------
# Create Event
# --------------------------------------------------

@app.post(
    "/events",
    response_model=EventResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_event(
    event_data: EventCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    event = Event(
        title=event_data.title,
        description=event_data.description,
        location=event_data.location,
        start_time=to_utc_naive(event_data.start_time),
        end_time=to_utc_naive(event_data.end_time),
        category=event_data.category,
        created_by=current_user.id,
        status="pending",
    )

    db.add(event)
    db.commit()
    db.refresh(event)

    return event


# --------------------------------------------------
# Get Approved Events + Search
# --------------------------------------------------



@app.get("/events", response_model=list[EventResponse])
def get_events(
    search: str | None = Query(default=None),
    category: str | None = Query(default=None),
    start_date: datetime | None = Query(default=None),
    end_date: datetime | None = Query(default=None),
    upcoming: bool = Query(
        default=False,
        description="Only show events that have not ended",
    ),
    db: Session = Depends(get_db),
):

    query = db.query(Event).filter(
        Event.status == "approved"
    )

    # Search by keyword
    if search and search.strip():
        search_term = f"%{search.strip()}%"

        query = query.filter(
            or_(
                Event.title.ilike(search_term),
                Event.description.ilike(search_term),
                Event.location.ilike(search_term),
            )
        )

    # Filter by category
    if category and category.strip():
        query = query.filter(
            Event.category.ilike(category.strip())
        )

    # Events starting on or after this date/time
    if start_date:
        if start_date.tzinfo is None:
            raise HTTPException(
                status_code=422,
                detail="start_date must include a timezone",
            )
        query = query.filter(
            Event.start_time >= to_utc_naive(start_date)
        )

    # Events starting before this date/time
    if end_date:
        if end_date.tzinfo is None:
            raise HTTPException(
                status_code=422,
                detail="end_date must include a timezone",
            )
        query = query.filter(
            Event.start_time < to_utc_naive(end_date)
        )

    # Only show events that have not ended
    if upcoming:
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        query = query.filter(
            Event.end_time > now
        )

    return query.order_by(Event.start_time.asc()).all()

# --------------------------------------------------
# Admin: Pending Events
# --------------------------------------------------

@app.get(
    "/admin/events/pending",
    response_model=list[EventResponse],
)
def get_pending_events(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return db.scalars(
        select(Event)
        .where(Event.status == "pending")
        .order_by(Event.start_time.asc())
    ).all()


# --------------------------------------------------
# Admin: Approve Event
# --------------------------------------------------

@app.patch(
    "/admin/events/{event_id}/approve",
    response_model=EventResponse,
)
def approve_event(
    event_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    event = db.get(Event, event_id)

    if not event:
        raise HTTPException(
            status_code=404,
            detail="Event not found",
        )

    event.status = "approved"

    db.commit()
    db.refresh(event)

    return event


# --------------------------------------------------
# Admin: Reject Event
# --------------------------------------------------

@app.patch(
    "/admin/events/{event_id}/reject",
    response_model=EventResponse,
)
def reject_event(
    event_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    event = db.get(Event, event_id)

    if not event:
        raise HTTPException(
            status_code=404,
            detail="Event not found",
        )

    event.status = "rejected"

    db.commit()
    db.refresh(event)

    return event


# --------------------------------------------------
# Save Event
# --------------------------------------------------

@app.post(
    "/users/me/saved-events/{event_id}",
    status_code=status.HTTP_201_CREATED,
)
def save_event(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    event = db.get(Event, event_id)

    if not event or event.status != "approved":
        raise HTTPException(
            status_code=404,
            detail="Event not found",
        )

    existing = db.scalar(
        select(SavedEvent).where(
            SavedEvent.user_id == current_user.id,
            SavedEvent.event_id == event_id,
        )
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Event already saved",
        )

    saved_event = SavedEvent(
        user_id=current_user.id,
        event_id=event_id,
    )

    db.add(saved_event)
    db.commit()

    return {"message": "Event saved successfully"}


# --------------------------------------------------
# Get Saved Events
# --------------------------------------------------

@app.get(
    "/users/me/saved-events",
    response_model=list[EventResponse],
)
def get_saved_events(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = (
        select(Event)
        .join(SavedEvent, SavedEvent.event_id == Event.id)
        .where(
            SavedEvent.user_id == current_user.id,
            Event.status == "approved",
        )
        .order_by(Event.start_time.asc())
    )

    return db.scalars(query).all()


# --------------------------------------------------
# Remove Saved Event
# --------------------------------------------------

@app.delete("/users/me/saved-events/{event_id}")
def remove_saved_event(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    saved_event = db.scalar(
        select(SavedEvent).where(
            SavedEvent.user_id == current_user.id,
            SavedEvent.event_id == event_id,
        )
    )

    if not saved_event:
        raise HTTPException(
            status_code=404,
            detail="Saved event not found",
        )

    db.delete(saved_event)
    db.commit()

    return {"message": "Event removed successfully"}
