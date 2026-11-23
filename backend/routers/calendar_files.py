"""Manual iCalendar import/export; does not need Google credentials."""
from datetime import date, datetime, time, timedelta, timezone
from io import BytesIO
from uuid import uuid4
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session
from icalendar import Calendar, Event as ICalEvent
from auth import get_current_user
from database import get_db
from models import User, CalendarCommitment, ScheduledEvent, Event

router = APIRouter(prefix='/calendar-files', tags=['calendar files'])
MAX_ICS_BYTES = 2 * 1024 * 1024
MAX_EVENTS = 1000

def normalize(value):
    if isinstance(value, date) and not isinstance(value, datetime):
        value = datetime.combine(value, time.min)
    if not isinstance(value, datetime):
        raise ValueError('Invalid calendar date')
    if value.tzinfo is None:
        raise ValueError('Timezone missing; export with timezone information')
    return value.astimezone(timezone.utc).replace(tzinfo=None)

@router.post('/import')
async def import_ics(file: UploadFile = File(...), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not (file.filename or '').lower().endswith('.ics'):
        raise HTTPException(400, 'Upload an .ics file')
    data = await file.read(MAX_ICS_BYTES + 1)
    if len(data) > MAX_ICS_BYTES:
        raise HTTPException(413, 'Calendar file too large')
    try:
        calendar = Calendar.from_ical(data)
        items = [item for item in calendar.walk() if item.name == 'VEVENT']
    except Exception:
        raise HTTPException(400, 'Invalid iCalendar file')
    if len(items) > MAX_EVENTS:
        raise HTTPException(413, 'Too many calendar events')
    imported, skipped = 0, 0
    for item in items:
        try:
            start = normalize(item.decoded('DTSTART'))
            if 'DTEND' in item:
                end = normalize(item.decoded('DTEND'))
            elif 'DURATION' in item:
                end = start + item.decoded('DURATION')
            else:
                end = start + timedelta(hours=1)
            if end <= start:
                raise ValueError('Invalid duration')
            uid = str(item.get('UID', ''))[:240]
            if not uid:
                uid = str(uuid4())
            external_id = 'ics:' + uid
            existing = db.scalar(select(CalendarCommitment).where(CalendarCommitment.user_id == user.id, CalendarCommitment.external_id == external_id))
            if existing is None:
                existing = CalendarCommitment(user_id=user.id, external_id=external_id, source='ics')
                db.add(existing)
            existing.title = str(item.get('SUMMARY', 'Busy'))[:200]
            existing.location = str(item.get('LOCATION', ''))[:200]
            existing.start_time = start
            existing.end_time = end
            imported += 1
        except (ValueError, TypeError, KeyError, OverflowError):
            skipped += 1
    db.commit()
    return {'imported_or_updated': imported, 'skipped': skipped, 'note': 'ICS import is a manual snapshot, not automatic Google Calendar sync'}

@router.get('/export')
def export_ics(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    calendar = Calendar()
    calendar.add('prodid', '-//Day Map//Student Schedule//EN')
    calendar.add('version', '2.0')
    entries = db.scalars(select(ScheduledEvent).where(ScheduledEvent.user_id == user.id)).all()
    for entry in entries:
        event = db.get(Event, entry.event_id)
        if not event or event.status != 'approved':
            continue
        item = ICalEvent()
        item.add('uid', f'daymap-event-{event.id}-user-{user.id}@daymap.local')
        item.add('summary', event.title)
        item.add('description', event.description)
        item.add('location', event.location)
        item.add('dtstart', event.start_time.replace(tzinfo=timezone.utc))
        item.add('dtend', event.end_time.replace(tzinfo=timezone.utc))
        item.add('dtstamp', datetime.now(timezone.utc))
        calendar.add_component(item)
    return Response(content=calendar.to_ical(), media_type='text/calendar', headers={'Content-Disposition': 'attachment; filename="daymap-schedule.ics"'})
