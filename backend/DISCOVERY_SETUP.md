# Day Map — No-Google-API backend update

This archive is an additive replacement for the **backend/** directory. It includes all files from the previously provided building-completion package plus new `routers/discovery.py`, discovery tests, and configurable hourly event refresh. It does not touch `frontend/`.

## Install

From repository root (stop uvicorn first):

```bash
cp -R backend backend-backup-before-discovery
unzip -o ~/Downloads/day-map-discovery-complete.zip -d ~/day-map
cd backend
source .venv/bin/activate
pip install -r requirements.txt
export DAYMAP_SECRET_KEY='YOUR_PERSISTENT_RANDOM_KEY'
uvicorn main:app --reload
```

Use your existing persistent secret, not the placeholder above. `.env.example` is documentation, not automatically loaded by the application. Do not commit secrets. Existing SQLite `daymap.db` is not included in the ZIP.

## New API (all require bearer JWT)

- `GET /discovery/recommendations?start=2026-11-24T09:00:00-05:00&end=2026-11-24T18:00:00-05:00` — approved events ranked by category interests and feasibility. Optional `category`, `include_unreachable`, `limit`.
- `GET /discovery/free-time?start=...&end=...&min_minutes=15` — gaps in a chosen window, using scheduled events and imported/manual commitments.
- `GET /discovery/feasibility/{event_id}` — `fits`, `tight`, `wont_make_it`, or `unknown`, with warnings and spare minutes.
- `GET /discovery/alternatives/{event_id}` — approved feasible alternatives near the original event's time, based on existing schedule without the original.
- `POST /discovery/swap/{event_id}` — `{ "replacement_event_id": 123, "override_conflicts": false }`. Replaces a scheduled event atomically; warns via 409 unless override enabled.
- `GET /discovery/reminders?within_minutes=60` — saved or scheduled events beginning soon. **Polling only**, no push/email delivery.

## Existing features preserved

Authentication, event submissions/admin approvals, Penn Engineering imports, schedule and conflict overrides, Valhalla walking/driving/cycling estimates, building seed scripts, RSVP/attendee visibility, networking/friends/blocks, messaging, and ICS import/export. Google Calendar OAuth code remains optional and requires Google Cloud configuration.

## Data setup

```bash
python -m services.seed_penn_buildings --preview
python -m services.seed_penn_buildings --apply
python -m services.seed_missing_buildings --preview
python -m services.seed_missing_buildings --apply
```

Verify building pins and entrance locations. Geocoding may fail or hit service limits; route estimates may be unavailable on the public Valhalla demo. Events need recognizable building names in `location` for walking feasibility.

## Refresh schedule

To enable Penn event imports on a **single** server process:

```bash
export DAYMAP_ENABLE_SCHEDULER=1
export DAYMAP_EVENT_REFRESH_HOURS=1
```

Hourly refresh is configurable from 1–24 hours. The importer can make multiple web requests per refresh; respect site rules and monitor errors. Avoid running it simultaneously in multiple server workers/reloader processes.

## Tests

```bash
python -m unittest discover -s tests -v
```

The 5 discovery tests use an isolated in-memory SQLite database. They were executed in a sandbox with a stub for the authentication dependency because the sandbox lacked `pwdlib`; the normal test command should work on your Mac where `requirements.txt` was installed. No live routing, OAuth, notifications, or complete FastAPI integration tests were run.

## Remaining work

- Actual local end-to-end tests: register/login, conflicts, route availability, friend/attendee permissions, messaging, calendar files, and discovery endpoints.
- Frontend map/timeline/fit indicators, event recommendations, alternatives and reminder display (teammates).
- Real notification delivery and read/unread reminder tracking are **not implemented**. Frontend can poll `/discovery/reminders` for now.
- Personalized ranking is category-based, **not machine learning**; it does not rank by precise proximity or social connections yet.
- Full Google Calendar OAuth sync needs partner Google Cloud credentials; ICS import/export works without them.
- Security hardening, migrations, abuse controls and production deployment remain.
