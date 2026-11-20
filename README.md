# Day Map

Day Map is a campus event discovery and scheduling application designed for University of Pennsylvania students. The goal is to help students discover events around campus, organize their schedules, and determine whether they have enough time to travel between activities.

The project is being developed for CIS 4120: Human-Computer Interaction.

## Features

### Backend — Implemented

- User registration and login with JWT authentication
- User profile retrieval and updates
- Event submission with admin approval
- Event search by title, description, or location
- Event filtering by category, date range, and upcoming status
- Saving and removing events from a user's account
- Automatic importing of events from the Penn Engineering calendar
- Event deduplication and updates using external source IDs
- Optional scheduled event refresh every six hours

### Frontend and Integration — In Progress

- Interactive campus map with event locations
- Event discovery and filtering interface
- Daily schedule and timeline
- Walking-time visualization between events
- Integration with the FastAPI backend

## Technology Stack

**Backend:** Python, FastAPI, SQLAlchemy, SQLite, Pydantic, APScheduler

**Frontend:** React Native / Expo

**Event Data:** Penn Engineering Events Calendar

## Project Structure

```text
day-map/
├── backend/
│   ├── main.py
│   ├── auth.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── requirements.txt
│   └── services/
│       ├── __init__.py
│       ├── penn_events.py
│       ├── scheduler.py
│       └── inspect_penn_event.py
└── README.md
```

The frontend directory is maintained separately on its development branch until integration.

## Backend Setup

### 1. Clone the repository

```bash
git clone https://github.com/Leo8806/day-map.git
cd day-map
git checkout backend
cd backend
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

On Windows:

```bash
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Set a secret key for JWT authentication:

```bash
export DAYMAP_SECRET_KEY="replace-with-a-long-random-secret"
```

Do not commit real secrets or `.env` files to GitHub.

### 5. Run the backend

From the `backend` directory:

```bash
uvicorn main:app --reload
```

The API will run at:

http://127.0.0.1:8000

Interactive API documentation:

http://127.0.0.1:8000/docs

The local SQLite database is created automatically.

## Importing Penn Engineering Events

Run the importer manually:

```bash
python -m services.penn_events
```

The importer retrieves Penn Engineering events and stores their titles, descriptions, locations, dates, and source URLs in the database.

Imported events are approved automatically. Existing imported events are updated instead of duplicated.

**Note:** The importer currently depends on an existing admin user with ID 2 in the local database. This needs to be configured before running the importer on a fresh installation.

### Automatic Refresh

To enable scheduled imports every six hours:

```bash
DAYMAP_ENABLE_SCHEDULER=1 uvicorn main:app
```

The backend must remain running for scheduled imports to execute.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Check API status |
| POST | `/auth/register` | Register a user |
| POST | `/auth/login` | Log in and receive a JWT |
| GET | `/users/me` | Retrieve current user |
| PATCH | `/users/me` | Update current user |
| GET | `/events` | Retrieve approved events |
| POST | `/events` | Submit an event |
| GET | `/admin/events/pending` | View pending submissions |
| PATCH | `/admin/events/{event_id}/approve` | Approve an event |
| PATCH | `/admin/events/{event_id}/reject` | Reject an event |
| GET | `/users/me/saved-events` | Retrieve saved events |
| POST | `/users/me/saved-events/{event_id}` | Save an event |
| DELETE | `/users/me/saved-events/{event_id}` | Remove a saved event |

### Event Filtering

The `/events` endpoint supports optional query parameters:

- `search`: Search titles, descriptions, and locations
- `category`: Filter by category
- `start_date`: Minimum event start date/time
- `end_date`: Exclusive maximum event start date/time
- `upcoming`: Only return events that have not ended

Example:

```text
GET /events?search=AI&category=Engineering&upcoming=true
```

Date/time filters must include timezone information.

## Authentication

Protected endpoints require a JWT access token:

```text
Authorization: Bearer YOUR_ACCESS_TOKEN
```

A token is returned by `POST /auth/login`.

Admin-only endpoints require an account with administrator permissions.

## Frontend Integration

The frontend should retrieve events using `GET /events` and connect the existing user authentication and saved-event endpoints.

During local development, the backend runs on port 8000.

When testing on a physical phone, use a reachable development-machine IP address or deployed API URL instead of `localhost`.

CORS configuration, API deployment, and explicit timezone formatting are planned integration improvements.

## Current Limitations

- Only Penn Engineering calendar events are imported automatically.
- The importer currently relies on a pre-existing admin user.
- Event timestamps are stored as UTC without explicit timezone suffixes in API responses.
- CORS has not yet been configured.
- Frontend integration is not yet complete.
- Google Calendar synchronization and walking-time calculations are not yet connected to the backend.
