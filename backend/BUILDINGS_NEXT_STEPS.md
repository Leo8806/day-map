# Penn building completion

This patch adds `services/seed_missing_buildings.py` and recognizes common Penn building aliases in route checks. It does not overwrite existing building records by default.

## Installation

Unzip this archive into the repository root (`~/day-map`). It contains the complete updated `backend/` tree. Back up the existing `backend/` folder first.

From `~/day-map/backend` with the Python virtual environment activated:

```bash
python -m services.seed_penn_buildings --apply
python -m services.seed_missing_buildings --preview
python -m services.seed_missing_buildings --apply
uvicorn main:app --reload
```

The first command seeds the 11 locations already identified by the original importer. The second previews the three missing buildings, and the third saves the available candidates. **Review map locations first**: the Huntsman and DRL coordinates are approximate map points, and the Singh point is derived from an address geocoder, not a surveyed building entrance. The Singh record is skipped if its address cannot be resolved; do not assume all 14 are present without checking `GET /buildings`.

For reliable routes, use the campus pedestrian entrance rather than the geometric building center. A public Valhalla instance is for low-volume testing only.

## Test

Start FastAPI, open `http://127.0.0.1:8000/docs`, and inspect `GET /buildings`. Test `POST /routes/estimate` with two building names. Events must have recognizable building names in their location fields; unknown locations remain unknown, not falsely marked reachable.

## Remaining portfolio requirements

A real end-to-end test of routing and messaging; verified building entrances; personalized free-time recommendations, alternatives/swap suggestions, reminders; frontend integration; and optional Google Calendar OAuth managed by teammates. Existing event discovery, RSVP, schedules, and messaging code has not been comprehensively tested.
