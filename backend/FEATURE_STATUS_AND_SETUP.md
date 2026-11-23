# Day Map backend: Penn buildings, routes, and messaging

This update is additive to the community/calendar backend. It does not change frontend files.

## Penn buildings

From `backend/` with the virtualenv activated:

```sh
python -m services.seed_penn_buildings --preview
```

The importer looks up 14 Penn landmarks using OpenStreetMap Nominatim, spaces requests by 1.1 seconds, and rejects results outside a broad campus bounding box. **Review the returned building names and locations** before running:

```sh
python -m services.seed_penn_buildings --apply
```

Missing/incorrect buildings must be entered or corrected manually. This script does **not** ship unverified coordinates, and its accuracy depends on OpenStreetMap. Do not repeatedly run it in a tight loop or use the public geocoder for bulk production traffic. Set a real contact in the User-Agent before broader use.

`GET /buildings` lists stored buildings. `POST /admin/buildings` adds individual buildings (requires admin). Existing building entries are not overwritten by the seed script.

## Walking routes

`DAYMAP_ROUTING_PROVIDER=valhalla` (default) calls a public Valhalla-compatible demo endpoint. Configure `DAYMAP_VALHALLA_URL` for a dedicated provider when deploying.

`GET /routes/estimate?origin_building_id=1&destination_building_id=2&mode=walking` requires login and returns duration in minutes, or a status explaining why the estimate is unavailable. Walking/driving/bicycling supported. No fabricated duration is returned on failure. Route data also feeds schedule conflict checks. For real campus travel, verify that routes are sensible and reflect pedestrian entrances.

## Private messaging

- `POST /messages/conversations` body `{ "recipient_id": 2 }`: create or reuse a one-to-one conversation.
- `GET /messages/conversations`: list your conversations.
- `GET /messages/conversations/{id}?limit=50&before_id=...`: paginated message history.
- `POST /messages/conversations/{id}` body `{ "text": "Hello!" }`: send a message.

Only accepted friends or users **both** opted into networking for the same event (with discoverable profiles) can start or continue messaging. Blocked pairs cannot view or send messages. Endpoints are authenticated and conversation membership is enforced.

**Not yet implemented**: live WebSockets/push notifications, read receipts, user reporting, spam throttling, retention/deletion tools, and production-grade abuse moderation. Do not deploy public messaging without these safeguards. This is an MVP messaging API, not a production messaging system.

## Portfolio requirements still to complete

Your portfolio's main idea is 'Can I actually make it?' The codebase has basic event search, personal schedules, travel warnings, overrides, and RSVP. Still needed and/or unverified:

- Feasibility statuses `fits`, `tight`, `won't make it` for **every** candidate event, considering travel from the preceding commitment and back to the next commitment.
- Nearby recommendations for available time gaps, interest-based ranking, and reachable-only filtering.
- Alternative events and a swap-event endpoint that resolves conflicts atomically.
- Event reminders and notifications.
- Frontend map pins, timelines, colors, and real API integration (teammates' responsibility).
- Google Calendar OAuth live sync (teammates to configure; manual ICS exists).
- Full integration tests and deployment checks.

## Setup

Back up your existing `backend/` before extracting the update. Install dependencies and start from `backend/`:

```sh
source .venv/bin/activate
pip install -r requirements.txt
export DAYMAP_ROUTING_PROVIDER=valhalla
uvicorn main:app --reload
```

The `DAYMAP_SECRET_KEY` must be set to a persistent, private, randomly generated value. See Swagger at `http://127.0.0.1:8000/docs`.

Database: new messaging tables are created via SQLAlchemy `create_all`. This is not a migration system; back up the SQLite database before upgrades.
