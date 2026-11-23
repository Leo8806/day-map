"""Portfolio-driven event discovery, feasibility, alternatives and reminders.

All timestamps in database are naive UTC. Routes may be unavailable; never
represent unknown travel time as a confirmed fit.
"""
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from auth import get_current_user
from database import get_db
from models import Event, User, SavedEvent, ScheduledEvent
from routers.planning import commitments, conflict_report, event_data, pref, travel, iso

router = APIRouter(prefix="/discovery", tags=["discovery"])


def aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise HTTPException(422, "Timestamps must include a timezone offset")
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def serialize(event: Event, report: dict, interest: bool = False) -> dict:
    if report["warnings"]:
        state = "wont_make_it"
    elif report["unverified_routes"]:
        state = "unknown"
    else:
        # Tight means there is little room for error, even if the buffer is met.
        spare = report.get("minimum_spare_minutes")
        state = "tight" if spare is not None and spare <= 5 else "fits"
    return {"event_id": event.id, "title": event.title, "description": event.description,
            "category": event.category, "location": event.location,
            "start_time": iso(event.start_time), "end_time": iso(event.end_time),
            "feasibility": state, "conflicts": report, "matches_interests": interest}


def evaluate(db: Session, user: User, event: Event, existing: list[dict]) -> dict:
    others = [x for x in existing if not (x["source"] == "daymap" and x["id"] == event.id)]
    report = conflict_report(db, user.id, event_data(event), others)
    # Calculate slack only for adjacent commitments, not every event in the day.
    before = max((x for x in others if x["end_time"] <= event.start_time),
                 key=lambda x: x["end_time"], default=None)
    after = min((x for x in others if x["start_time"] >= event.end_time),
                key=lambda x: x["start_time"], default=None)
    spare = []
    preference = pref(db, user.id)
    for first, second in ((before, event_data(event)), (event_data(event), after)):
        if first is None or second is None:
            continue
        route = travel(db, first, second, preference.mode)
        if route["minutes"] is not None:
            gap = (second["start_time"] - first["end_time"]).total_seconds() / 60
            spare.append(round(gap - route["minutes"] - preference.buffer_minutes, 1))
    report["minimum_spare_minutes"] = min(spare) if spare else None
    return report


def interests_of(user: User) -> set[str]:
    return {x.strip().casefold() for x in (user.interests or "").split(",") if x.strip()}


def rank(events: list[Event], user: User, db: Session, existing: list[dict],
         include_unreachable: bool) -> list[dict]:
    interests = interests_of(user)
    rows = []
    for event in events:
        report = evaluate(db, user, event, existing)
        matches = event.category.casefold() in interests
        item = serialize(event, report, matches)
        if not include_unreachable and item["feasibility"] not in ("fits", "tight"):
            continue
        rows.append(item)
    priority = {"fits": 0, "tight": 1, "unknown": 2, "wont_make_it": 3}
    rows.sort(key=lambda x: (not x["matches_interests"], priority[x["feasibility"]], x["start_time"], x["event_id"]))
    return rows


@router.get("/recommendations")
def recommendations(start: datetime | None = None, end: datetime | None = None,
                    category: str | None = None, include_unreachable: bool = True,
                    limit: int = Query(20, ge=1, le=100),
                    user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    beginning = aware_utc(start) if start else datetime.now(timezone.utc).replace(tzinfo=None)
    finish = aware_utc(end) if end else beginning + timedelta(days=7)
    if finish <= beginning or finish - beginning > timedelta(days=31):
        raise HTTPException(422, "Window must be positive and at most 31 days")
    query = select(Event).where(Event.status == "approved", Event.start_time >= beginning,
                                Event.end_time <= finish)
    if category:
        query = query.where(Event.category.ilike(category))
    events = db.scalars(query.order_by(Event.start_time).limit(500)).all()
    return rank(events, user, db, commitments(db, user.id), include_unreachable)[:limit]


@router.get("/free-time")
def free_time(start: datetime, end: datetime,
              min_minutes: int = Query(15, ge=1, le=1440),
              user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    beginning, finish = aware_utc(start), aware_utc(end)
    if finish <= beginning or finish - beginning > timedelta(days=7):
        raise HTTPException(422, "Window must be positive and at most 7 days")
    busy = sorted([(max(beginning, x["start_time"]), min(finish, x["end_time"]))
                   for x in commitments(db, user.id) if x["start_time"] < finish and x["end_time"] > beginning])
    gaps = []
    cursor = beginning
    for a, b in busy:
        if a > cursor and (a - cursor).total_seconds() >= min_minutes * 60:
            gaps.append({"start": iso(cursor), "end": iso(a), "minutes": int((a-cursor).total_seconds()//60)})
        cursor = max(cursor, b)
    if finish > cursor and (finish - cursor).total_seconds() >= min_minutes * 60:
        gaps.append({"start": iso(cursor), "end": iso(finish), "minutes": int((finish-cursor).total_seconds()//60)})
    return gaps


@router.get("/alternatives/{event_id}")
def alternatives(event_id: int, limit: int = Query(10, ge=1, le=50),
                 user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    original = db.get(Event, event_id)
    if not original or original.status != "approved":
        raise HTTPException(404, "Event not found")
    # If replacing an event already scheduled, omit it when evaluating candidates.
    existing = [x for x in commitments(db, user.id) if not (x["source"] == "daymap" and x["id"] == event_id)]
    window_start = original.start_time - timedelta(hours=2)
    window_end = original.end_time + timedelta(hours=2)
    events = db.scalars(select(Event).where(Event.status == "approved", Event.id != event_id,
                Event.start_time >= window_start, Event.end_time <= window_end).limit(500)).all()
    return rank(events, user, db, existing, include_unreachable=False)[:limit]


@router.get("/feasibility/{event_id}")
def feasibility(event_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    event = db.get(Event, event_id)
    if not event or event.status != "approved":
        raise HTTPException(404, "Event not found")
    return serialize(event, evaluate(db, user, event, commitments(db, user.id)),
                     event.category.casefold() in interests_of(user))


@router.get("/reminders")
def reminders(within_minutes: int = Query(60, ge=1, le=1440),
              user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Upcoming saved/scheduled events; frontend polls and handles local notifications.

    This endpoint does NOT send push notifications and does not track delivery.
    """
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    end = now + timedelta(minutes=within_minutes)
    scheduled = set(db.scalars(select(ScheduledEvent.event_id).where(ScheduledEvent.user_id == user.id)).all())
    saved = set(db.scalars(select(SavedEvent.event_id).where(SavedEvent.user_id == user.id)).all())
    ids = scheduled | saved
    if not ids:
        return []
    events = db.scalars(select(Event).where(Event.id.in_(ids), Event.status == "approved",
               Event.start_time >= now, Event.start_time <= end).order_by(Event.start_time)).all()
    return [{"event_id": e.id, "title": e.title, "location": e.location,
             "start_time": iso(e.start_time), "minutes_until": max(0, int((e.start_time-now).total_seconds()//60)),
             "scheduled": e.id in scheduled, "saved": e.id in saved} for e in events]


class SwapInput(BaseModel):
    replacement_event_id: int
    override_conflicts: bool = False


@router.post("/swap/{event_id}")
def swap_event(event_id: int, body: SwapInput,
               user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Atomically replace a scheduled event with an approved alternative."""
    original = db.scalar(select(ScheduledEvent).where(
        ScheduledEvent.user_id == user.id, ScheduledEvent.event_id == event_id))
    if not original:
        raise HTTPException(404, "Original event is not in your schedule")
    if event_id == body.replacement_event_id:
        raise HTTPException(422, "Choose a different event")
    replacement = db.get(Event, body.replacement_event_id)
    if not replacement or replacement.status != "approved":
        raise HTTPException(404, "Approved replacement event not found")
    if db.scalar(select(ScheduledEvent).where(ScheduledEvent.user_id == user.id,
                  ScheduledEvent.event_id == replacement.id)):
        raise HTTPException(409, "Replacement is already scheduled")
    others = [x for x in commitments(db, user.id) if not (x["source"] == "daymap" and x["id"] == event_id)]
    report = evaluate(db, user, replacement, others)
    if (report["warnings"] or report["unverified_routes"]) and not body.override_conflicts:
        raise HTTPException(409, {"message": "Replacement has conflicts or unverified travel", **report})
    db.delete(original)
    db.add(ScheduledEvent(user_id=user.id, event_id=replacement.id,
                          conflict_overridden=body.override_conflicts))
    db.commit()
    return {"removed_event_id": event_id, "added_event_id": replacement.id, "conflicts": report}
