# Day Map planning backend (integration branch)

## Run

From `backend/`:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export DAYMAP_SECRET_KEY='use-a-long-random-secret'
uvicorn main:app --reload
```

Visit http://127.0.0.1:8000/docs. Register and log in to obtain a bearer token. Existing SQLite databases receive the **new tables** automatically; existing tables are not modified. Back up the SQLite file before upgrading. For production use a proper migration system.

Demo seeding is now **off by default**. Set `DAYMAP_SEED_DEMO=1` only for local testing; never enable it on a public server. Existing seeded demo accounts in a previous database are **not** automatically removed. Provision real admins out-of-band; public registration never creates admins.

## Student schedule and warnings

- `GET /schedule`: scheduled events and imported/manual commitments, including conflict reports.
- `POST /schedule/check-conflict` body `{"event_id": 21}`: inspect warnings, no write.
- `POST /schedule/events` body `{"event_id": 21, "override_conflicts": false}`: add event. Returns HTTP 409 with warning details if conflicts or route verification uncertainty exist. Retry with `override_conflicts: true` after the user confirms. This is an explicit override, not an automatic bypass.
- `DELETE /schedule/events/{event_id}`: remove event from schedule, not bookmarks.
- `GET/PUT /users/me/travel-preferences`: `{"mode":"walking","buffer_minutes":5}`. Modes: walking, driving, bicycling, transit. Buffer 0–120 minutes.

The API compares event time intervals and route travel times plus buffer. Missing buildings, unsupported transit mode, or unavailable routes are reported as `unverified_routes`, **not** silently marked reachable. The frontend should warn the user about uncertainty and allow explicit override. Actual route ETA depends on the configured routing provider, mode and available route data. Driving duration does not account for parking; route durations are estimates, not guarantees. Add a parking allowance to the buffer as appropriate.

## Buildings and free OpenStreetMap routing

- `GET /buildings` lists registered buildings.
- `POST /admin/buildings` creates a building with `name`, `address`, `latitude`, `longitude` (admin only).
- Events are matched to building names in their `location` text. Populate Penn campus buildings with verified coordinates. Name matching is an MVP; explicit building IDs/aliases are future work.
- **Default:** `DAYMAP_ROUTING_PROVIDER=valhalla` uses the OpenStreetMap-based Valhalla service. No Google account or API key required. The default URL `https://valhalla1.openstreetmap.de/route` is a **public demo server**: it can be rate-limited or unavailable and is **not suitable for production traffic**. Do not bulk query it. Use `DAYMAP_VALHALLA_URL` for your own/dedicated Valhalla service before deployment.
- Supported Valhalla travel modes: walking, driving, bicycling. `transit` currently yields `route_unavailable` and requires a transit-capable provider; it is not estimated as driving.
- **Optional Google Maps:** set `DAYMAP_ROUTING_PROVIDER=google` and `GOOGLE_MAPS_API_KEY` with Directions API enabled. Keys stay on the backend.
- Missing or unavailable routes are returned in `unverified_routes`; users can explicitly override to add the event.
- Route calls currently have an eight-second timeout. Add caching and rate limiting before production.

## External calendar commitments

- `GET /calendar/commitments`
- `POST /calendar/commitments` body `{"title":"Class","location":"Levine Hall","start_time":"2026-11-24T14:00:00-05:00","end_time":"2026-11-24T15:00:00-05:00"}`
- `DELETE /calendar/commitments/{id}`

All inputs require timezone-aware ISO 8601 timestamps; the backend stores UTC. Schedule responses include explicit `+00:00` UTC offsets.

## Google Calendar (read-only MVP)

Set `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`, `GOOGLE_TOKEN_ENCRYPTION_KEY` (Fernet), and `DAYMAP_SECRET_KEY`. Register the exact callback URI in Google Cloud and enable Google Calendar API. Configure OAuth consent screen and test users as appropriate.

- Authenticated `GET /google-calendar/authorize` returns a Google authorization URL for the frontend to open.
- Google redirects to public `GET /google-calendar/callback?code=...&state=...`, which stores an encrypted refresh token.
- Authenticated `POST /google-calendar/sync` imports the next 90 days (configurable 1–365) of primary-calendar events as commitments.
- Authenticated `DELETE /google-calendar/disconnect` deletes stored connection and imported Google commitments.

Only read-only access is requested. Calendar sync is **manual**, not live or push-based. All-day Google events are currently normalized to UTC midnight rather than their original calendar timezone; improve this before relying on all-day conflict accuracy. The callback returns JSON rather than redirecting to a frontend deep link. Tokens are encrypted at rest using the provided Fernet key; secure your server, DB, key storage, and HTTPS in deployment. For production OAuth, add a one-time state nonce and replay protection.

## Profiles and friends

- Existing `GET/PATCH /users/me` endpoints handle name and interests.
- `GET /users/search?q=...` returns minimal public user fields (id/name).
- `POST /friends/requests/{receiver_id}` sends a request.
- `GET /friends/requests` lists incoming requests.
- `POST /friends/requests/{request_id}/accept` or `/decline` responds.
- `GET /friends` lists accepted friends.

## Frontend contract

Frontend should show `409` warning details and offer **Add Anyway** and **Cancel**. Saving/bookmarking an event through `/users/me/saved-events` is distinct from adding it to `/schedule/events`.

## Limitations and next work

This is an MVP implementation; it has been syntax-checked but **not end-to-end tested** against Google services. Set up tests, migrations, campus building aliases, route cache/quotas, more robust timezone handling for all-day events, and OAuth hardening before production. Do not use real private credentials in a public repository.
