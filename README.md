# Day Map

Day Map is a campus event discovery and scheduling application designed for University of Pennsylvania students. The goal is to help students discover events around campus, organize their schedules, and determine whether they have enough time to travel between activities.

The project is being developed for CIS 4120: Human-Computer Interaction.

## Features

### Backend

- User registration and login with JWT authentication
- User profile retrieval and updates
- Event submission with admin approval
- Event search by title, description, or location
- Event filtering by category, date range, and upcoming status
- Saving and removing events from a user's account
- Automatic importing of events from the Penn Engineering calendar
- Event deduplication and updates using external source IDs
- Optional scheduled event refresh every six hours

### Frontend

- Interactive campus map with event locations
- Event discovery and filtering interface
- Daily schedule and timeline
- Walking-time visualization between events

Connecting the Expo app to this API is in progress on `integrate-frontend-backend`.

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
│       ├── penn_events.py
│       ├── scheduler.py
│       └── inspect_penn_event.py
└── frontend/
```

## Run the app (Expo Go)

From the `frontend` folder:

```bash
cd frontend
npm install
npx expo login
```

Sign in with the same Expo account you use in Expo Go.

1. Install Expo Go from the App Store or Play Store.
2. Sign in to Expo Go.
3. On the Mac, from `frontend`, run `npx expo login` and sign in with that same account.
4. Connect the phone and the Mac to the same Wi-Fi.
5. Run `npx expo start`.
6. Scan the QR code. iPhone: Camera app. Android: the scanner inside Expo Go.

## Run the app (Xcode simulator)

1. Install Xcode from the App Store and open it once so it can finish setup.
2. From `frontend`, run `npx expo start`.
3. Press `i` to open the iOS Simulator.

If Xcode is installed and the simulator still will not start, run:

```bash
sudo xcode-select -s /Applications/Xcode.app/Contents/Developer
```

## Backend Setup

### 1. Create a virtual environment

From the `backend` directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

On Windows:

```bash
.venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Set a secret key for JWT authentication:

```bash
export DAYMAP_SECRET_KEY="replace-with-a-long-random-secret"
```

Do not commit real secrets or `.env` files to GitHub.

### 4. Run the backend

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
