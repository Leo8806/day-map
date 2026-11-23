"""Day Map student planning API. Times stored as naive UTC for compatibility with existing database."""
import os
import json
import math
from datetime import datetime, timezone
from typing import Any

import requests
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from auth import get_current_user, get_current_admin
from database import get_db
from models import (User, Event, ScheduledEvent, CalendarCommitment, Building,
                    TravelPreference, FriendRequest)
from schemas import (ScheduleAddInput, ScheduleCheckInput, CommitmentInput,
                     TravelPreferencesInput, BuildingInput)

router = APIRouter(tags=["planning"])


def utc(dt: datetime) -> datetime:
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


def iso(dt: datetime) -> str:
    return dt.replace(tzinfo=timezone.utc).isoformat()


def pref(db: Session, user_id: int) -> TravelPreference:
    return db.get(TravelPreference, user_id) or TravelPreference(user_id=user_id, mode="walking", buffer_minutes=5)


def find_building(db: Session, location: str) -> Building | None:
    # Match a building name against a structured location, e.g. "Houston Hall · 2nd floor".
    # Prefer longest names so that "Hall" does not shadow "Houston Hall".
    text = location.casefold()
    # Common event-calendar variants for the seeded Penn buildings.
    aliases = {
        "jon m. huntsman hall": "Huntsman Hall",
        "jon m huntsman hall": "Huntsman Hall",
        "drl": "David Rittenhouse Laboratory",
        "david rittenhouse lab": "David Rittenhouse Laboratory",
        "singh center": "Singh Center for Nanotechnology",
        "krishna p. singh center": "Singh Center for Nanotechnology",
    }
    for alias, canonical in aliases.items():
        if alias in text:
            match = db.scalar(select(Building).where(Building.name == canonical))
            if match:
                return match
    buildings = sorted(db.scalars(select(Building)).all(), key=lambda b: len(b.name), reverse=True)
    return next((b for b in buildings if b.name.casefold() in text), None)


def valhalla_eta(origin: Building, destination: Building, mode: str) -> int | None:
    """Route via a Valhalla-compatible OpenStreetMap service.

    The public demo server is suitable only for low-volume development testing.
    Configure DAYMAP_VALHALLA_URL to use a dedicated/self-hosted service.
    """
    costing = {"walking": "pedestrian", "driving": "auto", "bicycling": "bicycle"}.get(mode)
    if costing is None:
        return None  # Valhalla does not provide general public-transit routing here.
    url = os.getenv("DAYMAP_VALHALLA_URL", "https://valhalla1.openstreetmap.de/route")
    payload = {"locations": [
        {"lat": origin.latitude, "lon": origin.longitude},
        {"lat": destination.latitude, "lon": destination.longitude},
    ], "costing": costing, "units": "kilometers"}
    try:
        response = requests.get(url, params={"json": json.dumps(payload)}, timeout=8)
        response.raise_for_status()
        seconds = response.json()["trip"]["summary"]["time"]
        if not isinstance(seconds, (int, float)) or seconds < 0:
            return None
        return max(1, int(math.ceil(seconds / 60)))
    except (requests.RequestException, ValueError, KeyError, TypeError, OverflowError):
        return None


def google_eta(origin: str, destination: str, mode: str) -> int | None:
    key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not key:
        return None
    try:
        result = requests.get(
            "https://maps.googleapis.com/maps/api/directions/json",
            params={"origin": origin, "destination": destination, "mode": mode, "key": key},
            timeout=8,
        )
        result.raise_for_status()
        body = result.json()
        if body.get("status") != "OK":
            return None
        seconds = body["routes"][0]["legs"][0]["duration"]["value"]
        return max(1, (seconds + 59) // 60)
    except (requests.RequestException, ValueError, KeyError, IndexError, TypeError):
        return None


def travel(db: Session, first: dict, second: dict, mode: str) -> dict:
    a = find_building(db, first["location"]) if first["location"] else None
    b = find_building(db, second["location"]) if second["location"] else None
    if not a or not b:
        return {"minutes": None, "status": "unknown_location"}
    if a.id == b.id:
        return {"minutes": 0, "status": "ok", "provider": "same_building"}
    provider = os.getenv("DAYMAP_ROUTING_PROVIDER", "valhalla").lower()
    if provider == "google":
        mins = google_eta(f"{a.latitude},{a.longitude}", f"{b.latitude},{b.longitude}", mode)
    elif provider == "valhalla":
        mins = valhalla_eta(a, b, mode)
    else:
        return {"minutes": None, "status": "invalid_routing_provider"}
    return {"minutes": mins, "status": "ok" if mins is not None else "route_unavailable", "provider": provider}


def event_data(e: Event) -> dict:
    return {"id": e.id, "title": e.title, "location": e.location, "start_time": e.start_time, "end_time": e.end_time, "source": "daymap"}


def commitment_data(e: CalendarCommitment) -> dict:
    return {"id": e.id, "title": e.title, "location": e.location, "start_time": e.start_time, "end_time": e.end_time, "source": e.source}


def commitments(db: Session, user_id: int) -> list[dict]:
    entries = db.scalars(select(ScheduledEvent).where(ScheduledEvent.user_id == user_id)).all()
    result = []
    for entry in entries:
        event = db.get(Event, entry.event_id)
        if event and event.status == "approved":
            result.append({**event_data(event), "overridden": entry.conflict_overridden})
    result.extend(commitment_data(c) for c in db.scalars(select(CalendarCommitment).where(CalendarCommitment.user_id == user_id)).all())
    return sorted(result, key=lambda item: item["start_time"])


def conflict_report(db: Session, user_id: int, candidate: dict, others: list[dict] | None = None) -> dict:
    preference = pref(db, user_id)
    others = commitments(db, user_id) if others is None else others
    warnings = []
    unknown_routes = []
    # Only adjacent non-overlapping commitments need travel checks.
    before = max((x for x in others if x["end_time"] <= candidate["start_time"]),
                 key=lambda x: x["end_time"], default=None)
    after = min((x for x in others if x["start_time"] >= candidate["end_time"]),
                key=lambda x: x["start_time"], default=None)
    adjacent_ids = {id(x) for x in (before, after) if x is not None}
    for item in others:
        if candidate["start_time"] < item["end_time"] and item["start_time"] < candidate["end_time"]:
            overlap = (min(candidate["end_time"], item["end_time"]) - max(candidate["start_time"], item["start_time"])).total_seconds() / 60
            warnings.append({"type": "time_overlap", "with": item["title"], "source": item["source"], "minutes": round(overlap, 1)})
            continue
        if id(item) not in adjacent_ids:
            continue
        if item["end_time"] <= candidate["start_time"]:
            first, second = item, candidate
        elif candidate["end_time"] <= item["start_time"]:
            first, second = candidate, item
        else:
            continue
        available = (second["start_time"] - first["end_time"]).total_seconds() / 60
        route = travel(db, first, second, preference.mode)
        if route["minutes"] is None:
            unknown_routes.append({"with": item["title"], "reason": route["status"]})
        else:
            shortfall = route["minutes"] + preference.buffer_minutes - available
            if shortfall > 0:
                warnings.append({"type": "travel", "with": item["title"], "source": item["source"],
                                 "travel_minutes": route["minutes"], "buffer_minutes": preference.buffer_minutes,
                                 "available_minutes": round(available, 1), "shortfall_minutes": round(shortfall, 1)})
    return {"can_attend": not warnings and not unknown_routes, "has_conflict": bool(warnings),
            "travel_mode": preference.mode, "buffer_minutes": preference.buffer_minutes,
            "warnings": warnings, "unverified_routes": unknown_routes}


def approved_event(db: Session, event_id: int) -> Event:
    event = db.get(Event, event_id)
    if event is None or event.status != "approved":
        raise HTTPException(404, "Approved event not found")
    return event


@router.get("/schedule")
def get_schedule(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items = commitments(db, user.id)
    return [{**{**item, "start_time": iso(item["start_time"]), "end_time": iso(item["end_time"])},
             "conflicts": conflict_report(db, user.id, item, [x for x in items if x is not item])} for item in items]


@router.post("/schedule/check-conflict")
def check_conflict(body: ScheduleCheckInput, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    event = approved_event(db, body.event_id)
    return conflict_report(db, user.id, event_data(event), [x for x in commitments(db, user.id) if not (x["source"] == "daymap" and x["id"] == event.id)])


@router.post("/schedule/events", status_code=201)
def add_to_schedule(body: ScheduleAddInput, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    event = approved_event(db, body.event_id)
    if db.scalar(select(ScheduledEvent).where(ScheduledEvent.user_id == user.id, ScheduledEvent.event_id == event.id)):
        raise HTTPException(409, "Event already scheduled")
    report = conflict_report(db, user.id, event_data(event))
    if report["warnings"] and not body.override_conflicts:
        raise HTTPException(409, {"message": "Scheduling conflict; set override_conflicts=true to add anyway", **report})
    if report["unverified_routes"] and not body.override_conflicts:
        raise HTTPException(409, {"message": "Travel feasibility could not be verified; confirm to add anyway", **report})
    db.add(ScheduledEvent(user_id=user.id, event_id=event.id, conflict_overridden=body.override_conflicts))
    db.commit()
    return {"message": "Event added to schedule", "event_id": event.id, "conflicts": report}


@router.delete("/schedule/events/{event_id}")
def remove_from_schedule(event_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    row = db.scalar(select(ScheduledEvent).where(ScheduledEvent.user_id == user.id, ScheduledEvent.event_id == event_id))
    if not row:
        raise HTTPException(404, "Scheduled event not found")
    db.delete(row); db.commit()
    return {"message": "Event removed from schedule"}


@router.get("/users/me/travel-preferences")
def get_preferences(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    p = pref(db, user.id)
    return {"mode": p.mode, "buffer_minutes": p.buffer_minutes}


@router.put("/users/me/travel-preferences")
def update_preferences(body: TravelPreferencesInput, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    p = db.get(TravelPreference, user.id)
    if p is None:
        p = TravelPreference(user_id=user.id)
        db.add(p)
    p.mode = body.mode; p.buffer_minutes = body.buffer_minutes
    db.commit()
    return {"mode": p.mode, "buffer_minutes": p.buffer_minutes}


@router.get("/buildings")
def list_buildings(db: Session = Depends(get_db)):
    return db.scalars(select(Building).order_by(Building.name)).all()


@router.post("/admin/buildings", status_code=201)
def add_building(body: BuildingInput, admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    if db.scalar(select(Building).where(Building.name == body.name)):
        raise HTTPException(409, "Building already exists")
    b = Building(**body.model_dump()); db.add(b); db.commit(); db.refresh(b)
    return b


@router.post("/calendar/commitments", status_code=201)
def add_commitment(body: CommitmentInput, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    c = CalendarCommitment(user_id=user.id, title=body.title, location=body.location,
                           start_time=utc(body.start_time), end_time=utc(body.end_time))
    db.add(c); db.commit(); db.refresh(c)
    return {**commitment_data(c), "start_time": iso(c.start_time), "end_time": iso(c.end_time)}


@router.get("/calendar/commitments")
def list_commitments(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return [{**commitment_data(c), "start_time": iso(c.start_time), "end_time": iso(c.end_time)}
            for c in db.scalars(select(CalendarCommitment).where(CalendarCommitment.user_id == user.id)).all()]


@router.delete("/calendar/commitments/{commitment_id}")
def delete_commitment(commitment_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    c = db.get(CalendarCommitment, commitment_id)
    if c is None or c.user_id != user.id:
        raise HTTPException(404, "Commitment not found")
    db.delete(c); db.commit()
    return {"message": "Commitment deleted"}


@router.get("/users/search")
def user_search(q: str = Query(min_length=2, max_length=100), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    matches = db.scalars(select(User).where(User.id != user.id, or_(User.name.ilike(f"%{q}%"), User.email.ilike(f"%{q}%"))).limit(20)).all()
    return [{"id": x.id, "name": x.name} for x in matches]


@router.post("/friends/requests/{receiver_id}", status_code=201)
def request_friend(receiver_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if receiver_id == user.id or not db.get(User, receiver_id):
        raise HTTPException(400, "Invalid friend")
    existing = db.scalar(select(FriendRequest).where(or_(
        (FriendRequest.sender_id == user.id) & (FriendRequest.receiver_id == receiver_id),
        (FriendRequest.sender_id == receiver_id) & (FriendRequest.receiver_id == user.id))))
    if existing:
        raise HTTPException(409, "Friend request or friendship already exists")
    row = FriendRequest(sender_id=user.id, receiver_id=receiver_id, status="pending")
    db.add(row); db.commit(); db.refresh(row)
    return {"id": row.id, "status": row.status}


@router.get("/friends/requests")
def pending_requests(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(FriendRequest).where(FriendRequest.receiver_id == user.id, FriendRequest.status == "pending")).all()
    return [{"id": r.id, "sender_id": r.sender_id, "sender_name": db.get(User, r.sender_id).name} for r in rows]


@router.post("/friends/requests/{request_id}/accept")
def accept_request(request_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    row = db.get(FriendRequest, request_id)
    if row is None or row.receiver_id != user.id or row.status != "pending":
        raise HTTPException(404, "Pending friend request not found")
    row.status = "accepted"; db.commit()
    return {"message": "Friend request accepted"}


@router.post("/friends/requests/{request_id}/decline")
def decline_request(request_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    row = db.get(FriendRequest, request_id)
    if row is None or row.receiver_id != user.id or row.status != "pending":
        raise HTTPException(404, "Pending friend request not found")
    row.status = "declined"; db.commit()
    return {"message": "Friend request declined"}


@router.get("/friends")
def list_friends(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(FriendRequest).where(FriendRequest.status == "accepted", or_(FriendRequest.sender_id == user.id, FriendRequest.receiver_id == user.id))).all()
    friends = [db.get(User, r.receiver_id if r.sender_id == user.id else r.sender_id) for r in rows]
    return [{"id": x.id, "name": x.name} for x in friends if x]

@router.get('/routes/estimate')
def estimate_route(origin_building_id: int, destination_building_id: int,
                   mode: str = Query('walking', pattern='^(walking|driving|bicycling)$'),
                   user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Live route duration between two saved buildings; no Google credentials required."""
    origin, destination = db.get(Building, origin_building_id), db.get(Building, destination_building_id)
    if not origin or not destination:
        raise HTTPException(404, 'Building not found')
    result = travel(db, {'location': origin.name}, {'location': destination.name}, mode)
    return {'origin': origin.name, 'destination': destination.name, 'mode': mode, **result}
