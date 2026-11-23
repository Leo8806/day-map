"""Read-only Google Calendar OAuth and sync. Requires Google OAuth client and Fernet key."""
import os
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import jwt
import requests
from cryptography.fernet import Fernet
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import User, CalendarCommitment, GoogleCalendarConnection

router = APIRouter(prefix="/google-calendar", tags=["google-calendar"])
SCOPE = "https://www.googleapis.com/auth/calendar.readonly"


def config():
    values = [os.getenv(k) for k in ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REDIRECT_URI", "DAYMAP_SECRET_KEY", "GOOGLE_TOKEN_ENCRYPTION_KEY")]
    if not all(values):
        raise HTTPException(503, "Google Calendar integration is not configured")
    return values


def cipher(key: str):
    try:
        return Fernet(key.encode())
    except (ValueError, TypeError) as e:
        raise HTTPException(503, "Invalid GOOGLE_TOKEN_ENCRYPTION_KEY") from e


@router.get("/authorize")
def authorize(user: User = Depends(get_current_user)):
    client_id, _, redirect_uri, secret, _ = config()
    state = jwt.encode({"sub": str(user.id), "purpose": "google-calendar", "exp": datetime.now(timezone.utc) + timedelta(minutes=10)}, secret, algorithm="HS256")
    params = {"client_id": client_id, "redirect_uri": redirect_uri, "response_type": "code", "scope": SCOPE,
              "access_type": "offline", "prompt": "consent", "state": state}
    return {"authorization_url": "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)}


@router.get("/callback")
def callback(code: str, state: str, db: Session = Depends(get_db)):
    client_id, client_secret, redirect_uri, secret, encryption_key = config()
    try:
        payload = jwt.decode(state, secret, algorithms=["HS256"])
        if payload.get("purpose") != "google-calendar":
            raise ValueError("Invalid purpose")
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, ValueError, KeyError) as e:
        raise HTTPException(400, "Invalid or expired OAuth state") from e
    if not db.get(User, user_id):
        raise HTTPException(404, "User not found")
    try:
        response = requests.post("https://oauth2.googleapis.com/token", data={
            "code": code, "client_id": client_id, "client_secret": client_secret,
            "redirect_uri": redirect_uri, "grant_type": "authorization_code"}, timeout=12)
        response.raise_for_status()
        token = response.json().get("refresh_token")
    except (requests.RequestException, ValueError) as e:
        raise HTTPException(502, "Google OAuth token exchange failed") from e
    if not token:
        raise HTTPException(400, "Google did not provide offline access; reconnect with consent")
    row = db.get(GoogleCalendarConnection, user_id)
    if not row:
        row = GoogleCalendarConnection(user_id=user_id)
        db.add(row)
    row.refresh_token_encrypted = cipher(encryption_key).encrypt(token.encode()).decode()
    db.commit()
    return {"message": "Google Calendar connected. Return to Day Map and sync your calendar."}


def parse_google_date(value):
    # All-day events use YYYY-MM-DD; treat as midnight UTC (a documented simplification).
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


@router.post("/sync")
def sync_calendar(days: int = Query(default=90, ge=1, le=365), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    client_id, client_secret, _, _, encryption_key = config()
    connection = db.get(GoogleCalendarConnection, user.id)
    if not connection:
        raise HTTPException(404, "Google Calendar not connected")
    try:
        refresh = cipher(encryption_key).decrypt(connection.refresh_token_encrypted.encode()).decode()
        token_response = requests.post("https://oauth2.googleapis.com/token", data={
            "client_id": client_id, "client_secret": client_secret, "refresh_token": refresh,
            "grant_type": "refresh_token"}, timeout=12)
        token_response.raise_for_status()
        access_token = token_response.json()["access_token"]
        start = datetime.now(timezone.utc)
        end = start + timedelta(days=days)
        params = {"timeMin": start.isoformat(), "timeMax": end.isoformat(), "singleEvents": "true", "maxResults": 2500}
        url = "https://www.googleapis.com/calendar/v3/calendars/primary/events"
        imported = 0
        seen = set()
        while True:
            response = requests.get(url, headers={"Authorization": f"Bearer {access_token}"}, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            for item in data.get("items", []):
                if item.get("status") == "cancelled" or "start" not in item or "end" not in item:
                    continue
                external_id = "google:" + item["id"]
                start_dt = parse_google_date(item["start"].get("dateTime") or item["start"]["date"])
                end_dt = parse_google_date(item["end"].get("dateTime") or item["end"]["date"])
                existing = db.scalar(select(CalendarCommitment).where(CalendarCommitment.user_id == user.id, CalendarCommitment.external_id == external_id))
                if not existing:
                    existing = CalendarCommitment(user_id=user.id, external_id=external_id, source="google")
                    db.add(existing)
                existing.title = item.get("summary") or "Busy"
                existing.location = item.get("location", "")
                existing.start_time, existing.end_time = start_dt, end_dt
                seen.add(external_id)
                imported += 1
            if not data.get("nextPageToken"):
                break
            params["pageToken"] = data["nextPageToken"]
        # Remove deleted or moved Google events only inside the fetched window.
        old = db.scalars(select(CalendarCommitment).where(CalendarCommitment.user_id == user.id,
            CalendarCommitment.source == "google", CalendarCommitment.start_time >= start.replace(tzinfo=None),
            CalendarCommitment.start_time < end.replace(tzinfo=None))).all()
        for item in old:
            if item.external_id not in seen:
                db.delete(item)
        db.commit()
        return {"synced_events": imported, "window_days": days}
    except (requests.RequestException, ValueError, KeyError) as e:
        db.rollback()
        raise HTTPException(502, "Google Calendar sync failed") from e


@router.delete("/disconnect")
def disconnect(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    connection = db.get(GoogleCalendarConnection, user.id)
    if connection:
        db.delete(connection)
    for item in db.scalars(select(CalendarCommitment).where(CalendarCommitment.user_id == user.id, CalendarCommitment.source == "google")).all():
        db.delete(item)
    db.commit()
    return {"message": "Google Calendar disconnected and imported commitments removed"}
