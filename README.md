# Day Map Backend

Day Map is a campus event discovery and scheduling application designed to help University of Pennsylvania students find events, organize their schedules, and plan their day based on event locations and walking times.

This directory contains the backend API for Day Map, built using Python, FastAPI, SQLAlchemy, and SQLite.

## Tech Stack

- **Python** — Backend programming language
- **FastAPI** — REST API framework
- **SQLAlchemy** — Database models and queries
- **SQLite** — Local development database
- **Pydantic** — Request validation and response schemas
- **JWT** — User authentication
- **Argon2** — Password hashing through `pwdlib`
- **Uvicorn** — Development server

## Current Features

### User Authentication
- Register a new account with a name, email, and password.
- Prevent duplicate email registrations.
- Securely hash passwords before storing them.
- Log in using an email and password.
- Generate JWT access tokens for authenticated users.

### User Profiles
- Retrieve the currently authenticated user's profile.
- Update a user's display name and interests.
- Protect profile endpoints using JWT authentication.
- Store user information in the SQLite database.

### Database
- SQLAlchemy models for storing user information.
- SQLite database initialized automatically when the application starts.
- Event database model for storing campus event information (if Step 7 has been completed).

## Project Structure

```text
backend/
├── main.py          # FastAPI application and endpoints
├── database.py      # Database connection and session management
├── models.py        # SQLAlchemy database models
├── schemas.py       # Pydantic request and response schemas
├── auth.py          # Password hashing and JWT authentication
├── daymap.db        # Local SQLite database (not committed)
└── .venv/           # Python virtual environment (not committed)
```

## Getting Started

### 1. Navigate to the Backend Directory

```bash
cd day-map/backend
```

### 2. Create a Virtual Environment

```bash
python3 -m venv .venv
```

Activate the environment:

```bash
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install fastapi "uvicorn[standard]" sqlalchemy "pydantic[email]" "pwdlib[argon2]" PyJWT
```

### 4. Configure Authentication

Set the JWT secret key before starting the server:

```bash
export DAYMAP_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
```

This key is used to sign and verify authentication tokens. Do not commit secret keys to GitHub.

For local development, use a consistent secret key between server restarts if you want previously issued tokens to remain valid.

### 5. Start the Backend Server

```bash
uvicorn main:app --reload
```

The backend runs at:

http://127.0.0.1:8000

Interactive API documentation is available at:

http://127.0.0.1:8000/docs

## API Endpoints

### Implemented Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Welcome message |
| GET | `/health` | Check server status |
| POST | `/auth/register` | Register a new user |
| POST | `/auth/login` | Log in and receive an access token |
| GET | `/users/me` | Retrieve authenticated user's profile |
| PATCH | `/users/me` | Update authenticated user's profile |

### Example: Register a User

**POST `/auth/register`**

```json
{
  "name": "Test Student",
  "email": "student@example.com",
  "password": "TestPassword123!"
}
```

### Example: Log In

**POST `/auth/login`**

```json
{
  "email": "student@example.com",
  "password": "TestPassword123!"
}
```

A successful login returns an access token:

```json
{
  "access_token": "<JWT_ACCESS_TOKEN>",
  "token_type": "bearer"
}
```

Protected endpoints require the following HTTP header:

```text
Authorization: Bearer <JWT_ACCESS_TOKEN>
```

### Example: Update Profile

**PATCH `/users/me`**

```json
{
  "name": "Test Student Updated",
  "interests": "Robotics, Technology, Sports"
}
```

## Planned Features

### Event Management
- Allow authenticated users to submit campus events.
- Store event titles, descriptions, locations, categories, and times.
- Allow administrators to approve or reject submitted events.
- Display only approved events publicly.
- Allow users to save events to personal schedules.

### Google Maps Integration
- Display campus event locations on an interactive map.
- Provide event pins and location details.
- Calculate walking routes and estimated travel times.
- Determine whether students can reach events on time.

### Google Calendar Integration
- Connect user Google accounts using OAuth.
- Retrieve calendar events and existing commitments.
- Identify scheduling conflicts.
- Add selected events to users' Google Calendars.

### Scheduling
- Build personalized daily schedules.
- Calculate feasibility based on event times and walking distances.
- Display scheduling conflicts and travel-time warnings.
- Allow users to override scheduling conflicts.

### Frontend Integration
- Connect the React Native/Expo frontend to FastAPI.
- Integrate authentication, user profiles, events, maps, and scheduling.
- Test complete workflows across frontend and backend.

## Development Notes

- The backend currently runs locally.
- SQLite is used for development and prototyping.
- The local database and virtual environment should not be committed to GitHub.
- API endpoints can be tested using FastAPI's interactive Swagger documentation.
- The frontend is being developed separately using React Native, Expo, and TypeScript.
