import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from database import Base, engine, get_db, SessionLocal
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

DEMO_EMAIL = "demo@daymap.app"
DEMO_PASSWORD = "daymap-demo"


def seed_demo_data() -> None:
    """Create a demo student and today's sample events when the database is empty."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == DEMO_EMAIL).first()
        if user is None:
            user = User(
                name="Demo Student",
                email=DEMO_EMAIL,
                password_hash=password_hash.hash(DEMO_PASSWORD),
                is_admin=True,
                interests="Career,Research",
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        if db.query(Event).count() > 0:
            return

        today = datetime.now().replace(second=0, microsecond=0)

        def at(hour: int, minute: int) -> datetime:
            return today.replace(hour=hour, minute=minute)

        samples = [
            ("Biotech coffee chat", "Meet students and researchers in biotech.", "Houston Hall · 2nd floor", at(12, 30), at(13, 15), "Career"),
            ("Grad info session", "Hear from current students about programs and labs.", "Houston Hall · 2nd floor", at(13, 5), at(13, 50), "Academic"),
            ("Econ open house", "An open house for economics students.", "Houston Hall · 1st floor", at(13, 40), at(14, 30), "Social"),
            ("Research drop-in", "Drop in to talk with lab groups.", "Huntsman · 2nd floor", at(12, 30), at(13, 0), "Research"),
            ("Bioeng lab tour", "A short tour of the bioengineering lab.", "Towne · 2nd floor", at(13, 20), at(13, 50), "Research"),
            ("Student reading group", "A reading group in the library.", "Van Pelt · 1st floor", at(13, 30), at(14, 30), "Academic"),
            ("Biotech panel", "A panel that runs into the 2:00 lab.", "Levine", at(13, 20), at(14, 0), "Research"),
        ]
        for title, description, location, start, end, category in samples:
            db.add(
                Event(
                    title=title,
                    description=description,
                    location=location,
                    start_time=start,
                    end_time=end,
                    category=category,
                    created_by=user.id,
                    status="approved",
                    source="seed",
                )
            )
        db.commit()
    finally:
        db.close()


seed_demo_data()


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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
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

    token = create_access_token(user.id)

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
