# Day Map — Backend

Day Map is a Penn campus-event discovery and scheduling app. Its core goal is to help students answer **“Can I actually make it?”** by combining events, personal commitments, building locations, and estimated travel times. This README covers the Python backend; the React Native/Expo frontend is maintained separately.

## Stack

- Python, FastAPI, Pydantic
- SQLAlchemy with SQLite for local development
- JWT authentication
- Penn Engineering event importer (BeautifulSoup/requests) and optional APScheduler refresh
- OpenStreetMap-derived building geocoding and Valhalla routing (public demo endpoint for development)
- `.ics` calendar import/export

## Features in the current backend code

- **Accounts:** registration, login, JWT, user profiles and travel preferences.
- **Events:** search/filter, save/bookmark, submit for admin review, approve/reject, import Penn Engineering events.
- **Scheduling:** add/remove events, manual/imported commitments, time-overlap and travel-time warnings, configurable buffer, explicit **Add Anyway** override.
- **Campus travel:** building records, seed scripts, walking/driving/cycling route estimates, unknown-route handling.
- **Discovery:** free-time gaps, interest/category-based recommendations, feasibility (`fits`, `tight`, `wont_make_it`, `unknown`), alternative events, schedule swaps.
- **Community:** RSVP, attendee counts and opt-in visibility, public profiles, friend requests, blocking, opt-in event networking, private one-to-one messaging.
- **Calendars:** manual `.ics` import/export; optional Google Calendar OAuth code (not configured).
- **Reminders:** endpoint listing upcoming events; no push/email notifications.

**Status:** These are code implementations, **not yet verified end-to-end**. Do not describe them as production-ready. The frontend may still use mock data or lack screens for some endpoints.

## Local setup

From the repository root:

```bash
cd backend
python3 -m venv .venv  # skip if already created
source .venv/bin/activate
pip install -r requirements.txt
```

Generate a persistent random signing key **once**, store it privately, and load it into the terminal environment:

```bash
python3 -c 'import secrets; print(secrets.token_hex(32))'
export DAYMAP_SECRET_KEY='PASTE_GENERATED_KEY_HERE'
export DAYMAP_ROUTING_PROVIDER=valhalla
uvicorn main:app --reload
```

The export applies to the current terminal session. Keep the same signing key across restarts, and **never commit it**. The `.env.example` file documents settings; copying it alone does not guarantee that it will be loaded.

Open:
- API docs: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/health

Register, log in, and use the returned bearer token to test protected endpoints in Swagger.

## Building setup and routes

From `backend/` with the virtual environment active:

```bash
python -m services.seed_penn_buildings --preview
python -m services.seed_penn_buildings --apply
python -m services.seed_missing_buildings --preview
python -m services.seed_missing_buildings --apply
```

Check the output before saving and verify pins/entrances. Some names may not geocode, and approximate coordinates may require correction. Building names in imported event locations must match stored buildings for route-based feasibility to work.

Test `GET /buildings` and authenticated `GET /routes/estimate` in Swagger. Valhalla's default public endpoint is for low-volume development; it can fail or rate-limit. When a route cannot be verified, the backend should return an unknown/unverified result, not invent a duration.

## Key API endpoints

| Area | Endpoints |
|---|---|
| Authentication | `POST /auth/register`, `POST /auth/login` |
| Events | `GET /events`, `POST /events`, admin approval routes |
| Schedule | `GET /schedule`, `POST /schedule/check-conflict`, `POST /schedule/events`, `DELETE /schedule/events/{event_id}` |
| Preferences | `GET/PUT /users/me/travel-preferences` |
| Buildings/routes | `GET /buildings`, `GET /routes/estimate` |
| Discovery | `GET /discovery/recommendations`, `/discovery/free-time`, `/discovery/feasibility/{event_id}`, `/discovery/alternatives/{event_id}`, `/discovery/reminders` |
| Schedule swap | `POST /discovery/swap/{event_id}` |
| Attendance | `PUT /events/{event_id}/rsvp`, `DELETE /events/{event_id}/rsvp`, `GET /events/{event_id}/attendees`, `GET /events/{event_id}/networking` |
| Profiles/friends | `PUT /users/me/public-profile`, `GET /users/{user_id}/public-profile`, friend request routes |
| Messaging | `POST /messages/conversations`, `GET /messages/conversations`, `GET/POST /messages/conversations/{id}` |
| Calendar files | `POST /calendar-files/import`, `GET /calendar-files/export` |

Swagger is the source of truth for request bodies, parameters, and response schemas.

### Conflict behavior

A student can check an event without adding it. Adding a conflicting event normally returns a `409` warning. The frontend should show the warning and offer **Add Anyway** (retry with `override_conflicts: true`) or **Cancel**. Saving an event, scheduling it, and RSVPing are separate actions.

## Penn event refresh

To opt into hourly refresh on **one** server process:

```bash
export DAYMAP_ENABLE_SCHEDULER=1
export DAYMAP_EVENT_REFRESH_HOURS=1
```

Use the importer responsibly; one refresh can involve multiple website requests. Avoid duplicate schedulers across workers or reload processes.

## Testing

Run the included isolated discovery tests:

```bash
cd backend
source .venv/bin/activate
python -m unittest discover -s tests -v
```

Then test the following manually in Swagger and with the frontend: registration/login; admin-approved event import; buildings and live routes; conflict warning and override; free-time/recommendations/alternatives/swap; RSVP and attendee privacy; friend requests, blocking and messaging permissions; `.ics` import/export; reminder feed. Back up the SQLite database before schema changes. SQLAlchemy `create_all` creates new tables but **does not migrate existing table columns**.

## Remaining work / team responsibilities

**Frontend integration:** Replace demo data with API responses. Complete the campus map and event pins, building sheet, event detail, My Day timeline, `fits/tight/won't make it` states, Add Anyway confirmation, alternatives/swap flow, profile, RSVP/attendee, networking, messaging, and reminders UI. Validate the complete user flow on a real device.

**Google Calendar:** Teammates can configure Google Cloud OAuth and Calendar API for account connection/sync. Until then, users can manually import/export `.ics` files. Existing Google OAuth code is optional and has not been validated with real credentials.

**Notifications:** The reminder feed exists, but push/email notifications and delivery scheduling do not.

**Before release:** Add full integration tests, database migrations, secure production configuration, rate limiting/abuse controls for messaging, route caching/provider capacity, accurate time zone handling, and security/privacy review. Live messaging via WebSockets, read receipts, and moderation/reporting are not included in this MVP.

## AI/tool usage

Development included assistance from ChatGPT for drafting and reviewing backend code, documentation, and tests. All generated changes require local verification and team review before submission or deployment.
