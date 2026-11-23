# Day Map community and calendar file API

All endpoints require Bearer JWT. RSVP is independent of bookmarks and schedule additions.

- `PUT /events/{event_id}/rsvp`: `{ "visible": false, "networking": false }`. Private by default. Networking requires both visible RSVP and discoverable public profile.
- `DELETE /events/{event_id}/rsvp`: cancel RSVP.
- `GET /events/{event_id}/attendees`: total RSVP count and opt-in visible profiles (subject to blocks).
- `GET /events/{event_id}/networking`: only opted-in event networkers can see other opted-in attendees.
- `PUT /users/me/public-profile`: `{ "major": "Computer Science", "graduation_year": 2028, "bio": "...", "interests": "robotics", "discoverable": true }`.
- `GET /users/{user_id}/public-profile`: discoverable profiles only (or self).
- `POST /users/{user_id}/block`, `DELETE /users/{user_id}/block`: block/unblock discovery.
- `POST /calendar-files/import`: multipart upload with `file` field, max 2 MB, max 1000 events. Imports timezone-aware VEVENTs as private commitments; reimporting the same UID updates them. Skips malformed events.
- `GET /calendar-files/export`: downloads the user's scheduled Day Map events as `daymap-schedule.ics`.

## Using Google Calendar without Google Cloud

In Google Calendar on desktop: Settings > Import & export > Export. Unzip the downloaded archive and upload an `.ics` file to `/calendar-files/import`. For export, download `/calendar-files/export`, then use Google Calendar Settings > Import & export > Import. These are manual snapshots, not live sync. Automated Google Calendar OAuth still needs Google Cloud credentials.

## Important limitations

- Existing SQLite tables are not migrated by `create_all`; this change adds new tables only. Back up `daymap.db` first.
- Event and calendar times use UTC-naive storage. ICS timestamps are converted to UTC before storage. A timezone-naive ICS timestamp is skipped to avoid silently scheduling at the wrong time.
- The public Valhalla endpoint is for development, not guaranteed production routing.
- No chat messaging or event-specific friend invitations yet. Existing friend-request APIs are in `routers/planning.py`.
- These endpoints require integration tests and security review before deployment.
