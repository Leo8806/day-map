
# Day Map

Day Map is a campus event discovery and scheduling application designed for students at the University of Pennsylvania.

Our goal is to help students discover events around campus, organize their schedules, and answer one important question:

**"Can I actually make it?"**

Day Map combines campus events, personal schedules, building locations, and estimated travel times to help students determine whether they can attend events without conflicting with their existing commitments.

This project is being developed for **CIS 4120: Human-Computer Interaction** at the University of Pennsylvania.

## Features

### Event Discovery

- Interactive campus map displaying event locations
- Search events by title, description, or location
- Filter events by category, date, and upcoming status
- View event details, locations, and times
- Save and bookmark events
- Automatically import events from the Penn Engineering calendar
- Submit events for administrator approval
- Update imported events without creating duplicates

### Personal Scheduling

- Create and manage a personal daily schedule
- Add or remove campus events
- Add manual commitments, including classes and meetings
- Import existing calendar commitments
- Detect overlapping events and scheduling conflicts
- Estimate travel times between locations
- Configure travel-time buffers
- Display event feasibility as:
  - **Fits:** Enough time to attend and travel
  - **Tight:** Possible, but limited extra time
  - **Won't Make It:** Conflicts with an existing commitment or travel requirements
  - **Unknown:** Not enough location or routing information
- Allow users to override conflicts with an **Add Anyway** option
- Suggest alternative events when scheduling conflicts occur
- Swap scheduled events for alternatives

### Personalized Recommendations

- Recommend events based on user interests and categories
- Identify free-time gaps between commitments
- Suggest events that fit into available time
- Consider scheduling conflicts and travel feasibility
- Help users discover nearby events they might otherwise miss

### Campus Navigation

- Store campus building names and coordinates
- Recognize alternative building names and abbreviations
- Estimate walking, driving, and cycling routes
- Use OpenStreetMap-based geocoding and Valhalla routing
- Handle unavailable routes without inventing travel times

### Social and Networking

- RSVP to events
- View event attendee counts
- See attendees who have opted into visibility
- Create and update public profiles
- Send and accept friend requests
- Block other users
- Discover other students attending the same events
- Opt into event-based networking
- Send private one-to-one messages

### Calendar Integration

- Import calendar events using `.ics` files
- Export schedules as `.ics` files
- Google Calendar OAuth integration scaffolded but not yet configured
- Retrieve upcoming scheduled events through a reminder endpoint

Actual push notifications and automatic Google Calendar synchronization are not yet implemented.

## Technology Stack

**Backend**
- Python
- FastAPI
- SQLAlchemy
- SQLite
- Pydantic
- JWT authentication
- BeautifulSoup and Requests
- APScheduler
- Valhalla Routing API
- OpenStreetMap / Nominatim
- iCalendar

**Frontend**
- React Native
- Expo

**Event Data**
- Penn Engineering Events Calendar

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
│   ├── routers/
│   │   ├── planning.py
│   │   ├── community.py
│   │   ├── messaging.py
│   │   ├── calendar_files.py
│   │   └── google_calendar.py
│   ├── services/
│   │   ├── penn_events.py
│   │   ├── scheduler.py
│   │   ├── inspect_penn_event.py
│   │   ├── seed_penn_buildings.py
│   │   └── seed_missing_buildings.py
│   └── tests/
├── frontend/
├── README.md
└── .gitignore
```

The project structure may include additional backend services and routers as development continues.

## Running the Frontend

### Expo Go

From the frontend directory:

```bash
cd frontend
npm install
npx expo login
```

Sign in using the same Expo account used on your mobile device.

1. Install Expo Go from the App Store or Google Play Store.
2. Sign in to Expo Go.
3. Connect your phone and computer to the same Wi-Fi network.
4. Run:

```bash
npx expo start
```

5. Scan the QR code using your phone.

On iPhone, use the Camera app. On Android, use the scanner inside Expo Go.

### Xcode Simulator

1. Install Xcode from the Mac App Store.
2. Open Xcode once to finish setup.
3. From the frontend directory, run:

```bash
npx expo start
```

4. Press `i` to launch the iOS Simulator.

If the simulator does not start, run:

```bash
sudo xcode-select -s /Applications/Xcode.app/Contents/Developer
```

## Backend Setup

### 1. Create a Virtual Environment

Navigate to the backend directory:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
```

On Windows:

```bash
.venv\Scripts\activate
```

If a virtual environment already exists, activate it without recreating it.

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Generate a secure JWT signing key:

```bash
python3 -c 'import secrets; print(secrets.token_hex(32))'
```

Copy the generated value and configure:

```bash
export DAYMAP_SECRET_KEY="YOUR_GENERATED_SECRET_KEY"
export DAYMAP_ROUTING_PROVIDER=valhalla
```

Use the same secret key across server restarts.

Never commit secret keys or `.env` files to GitHub.

### 4. Start the Backend

From the backend directory:

```bash
uvicorn main:app --reload
```

The API runs locally at:

http://127.0.0.1:8000

Interactive API documentation:

http://127.0.0.1:8000/docs

Health check:

http://127.0.0.1:8000/health

The SQLite database is initialized locally.

## Importing Penn Engineering Events

Day Map imports events from the Penn Engineering Events Calendar.

The importer retrieves available event information, including:

- Event title
- Description
- Location
- Start and end times
- Source URL
- External source identifier

Imported events are automatically approved and existing events are updated rather than duplicated.

To run the importer manually:

```bash
python -m services.penn_events
```

**Note:** The original importer relied on an administrator account with ID 2. This dependency should be verified before running the importer on a fresh database.

### Automatic Event Refresh

Scheduled event imports can be enabled using:

```bash
export DAYMAP_ENABLE_SCHEDULER=1
export DAYMAP_EVENT_REFRESH_HOURS=1
uvicorn main:app
```

This configuration requests hourly refreshes.

The backend must remain running for automatic refresh to work. Avoid running duplicate schedulers across multiple server processes.

## Campus Building Setup

Day Map uses stored campus building locations to estimate travel times.

To preview building coordinates:

```bash
python -m services.seed_penn_buildings --preview
python -m services.seed_missing_buildings --preview
```

To save them:

```bash
python -m services.seed_penn_buildings --apply
python -m services.seed_missing_buildings --apply
```

The building database includes locations such as:

- Houston Hall
- Huntsman Hall
- Van Pelt Library
- Levine Hall
- Towne Building
- College Hall
- Fisher Fine Arts Library
- Williams Hall
- David Rittenhouse Laboratory
- Singh Center for Nanotechnology
- Penn Museum
- Meyerson Hall
- Hill College House
- Annenberg Center

Coordinates should be verified before relying on them for travel estimates.

## API Endpoints

The backend provides REST endpoints for authentication, event discovery, scheduling, routing, recommendations, and networking.

### Authentication and Profiles

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/register` | Register a user |
| POST | `/auth/login` | Log in and receive a JWT |
| GET | `/users/me` | Retrieve the current user |
| PATCH | `/users/me` | Update the current user |
| GET | `/users/me/travel-preferences` | Retrieve travel preferences |
| PUT | `/users/me/travel-preferences` | Update travel preferences |

### Events

| Method | Endpoint | Description |
|---|---|---|
| GET | `/events` | Retrieve approved events |
| POST | `/events` | Submit an event |
| GET | `/admin/events/pending` | View pending events |
| PATCH | `/admin/events/{event_id}/approve` | Approve an event |
| PATCH | `/admin/events/{event_id}/reject` | Reject an event |
| GET | `/users/me/saved-events` | Retrieve saved events |
| POST | `/users/me/saved-events/{event_id}` | Save an event |
| DELETE | `/users/me/saved-events/{event_id}` | Remove a saved event |

Event filtering supports search, category, date ranges, and upcoming events.

Example:

```text
GET /events?search=AI&category=Engineering&upcoming=true
```

### Scheduling

| Method | Endpoint | Description |
|---|---|---|
| GET | `/schedule` | Retrieve the user's schedule |
| POST | `/schedule/check-conflict` | Check scheduling conflicts |
| POST | `/schedule/events` | Add an event to the schedule |
| DELETE | `/schedule/events/{event_id}` | Remove a scheduled event |

### Buildings and Routing

| Method | Endpoint | Description |
|---|---|---|
| GET | `/buildings` | Retrieve campus buildings |
| GET | `/routes/estimate` | Estimate travel between locations |
| POST | `/routes/estimate` | Estimate a route using coordinates |

The available routing endpoints and request formats can be confirmed in Swagger.

### Discovery and Recommendations

| Method | Endpoint | Description |
|---|---|---|
| GET | `/discovery/recommendations` | Recommend events |
| GET | `/discovery/free-time` | Find available time windows |
| GET | `/discovery/feasibility/{event_id}` | Check event feasibility |
| GET | `/discovery/alternatives/{event_id}` | Find alternative events |
| POST | `/discovery/swap/{event_id}` | Swap scheduled events |
| GET | `/discovery/reminders` | Retrieve upcoming reminders |

### Community and Networking

| Method | Endpoint | Description |
|---|---|---|
| PUT | `/events/{event_id}/rsvp` | RSVP to an event |
| DELETE | `/events/{event_id}/rsvp` | Remove an RSVP |
| GET | `/events/{event_id}/attendees` | Retrieve visible attendees |
| GET | `/events/{event_id}/networking` | Discover event networking |
| PUT | `/users/me/public-profile` | Update public profile |
| GET | `/users/{user_id}/public-profile` | View public profile |

Additional endpoints support friend requests and blocking.

### Messaging

| Method | Endpoint | Description |
|---|---|---|
| POST | `/messages/conversations` | Start a conversation |
| GET | `/messages/conversations` | List conversations |
| GET | `/messages/conversations/{id}` | Retrieve messages |
| POST | `/messages/conversations/{id}` | Send a message |

Messaging permissions depend on friendship or mutual event-networking eligibility.

### Calendar Files

| Method | Endpoint | Description |
|---|---|---|
| POST | `/calendar-files/import` | Import an `.ics` file |
| GET | `/calendar-files/export` | Export a calendar file |

For complete request bodies, parameters, and response formats, use the FastAPI Swagger documentation.

## Scheduling Conflict Detection

One of Day Map's main features is determining whether a student can realistically attend an event.

The backend considers:

1. The event's start and end times.
2. Existing scheduled commitments.
3. Travel time from the previous commitment.
4. Travel time to the next commitment.
5. User-configured travel buffers.

Events can be classified as:

- **Fits:** The event can be attended without a detected conflict.
- **Tight:** The schedule is feasible but has limited spare time.
- **Won't Make It:** The event conflicts with another commitment or travel requirements.
- **Unknown:** The system cannot reliably determine feasibility.

If an event conflicts with the user's schedule, the frontend should display a warning and allow the user to cancel or select **Add Anyway**.

Saving an event, adding it to a schedule, and RSVPing are separate actions.

## Authentication

Protected API endpoints require a JWT access token:

```text
Authorization: Bearer YOUR_ACCESS_TOKEN
```

Tokens are returned after a successful login.

Administrator endpoints require administrator permissions.

## Frontend Integration

The React Native/Expo frontend should connect to the backend for:

- Authentication and profiles
- Event discovery and filtering
- Interactive campus map and building information
- Event details and RSVPs
- Personal schedules and calendar commitments
- Walking-time estimates
- Conflict warnings and overrides
- Personalized recommendations
- Free-time discovery
- Alternative events and schedule swaps
- Networking and messaging
- Upcoming-event reminders

The integration branch is:

`integrate-frontend-backend`

When testing on a physical phone, use the computer's reachable local IP address or a deployed API URL rather than `localhost`.

## Testing

Run the included discovery unit tests:

```bash
cd backend
source .venv/bin/activate
python -m unittest discover -s tests -v
```

Then test the full application workflow:

1. Register and log in.
2. Import and retrieve campus events.
3. Verify campus buildings and travel estimates.
4. Add events and commitments to a schedule.
5. Test conflict warnings and Add Anyway.
6. Retrieve recommendations and free-time opportunities.
7. Test alternatives and schedule swaps.
8. RSVP and view attendee information.
9. Test friends, networking, and private messaging.
10. Import and export calendar files.
11. Retrieve upcoming reminders.
12. Connect and test the frontend.

These features have been implemented in backend code but have not all been verified end to end.

## Remaining Work

### Frontend

- Complete backend integration
- Replace remaining mock data with live API responses
- Display event pins and event details on the campus map
- Complete the My Day timeline
- Display feasibility and travel-time warnings
- Support conflict overrides and alternative suggestions
- Connect profiles, attendees, networking, and messaging
- Test the complete app on a physical device

### Google Calendar

- Configure Google Cloud credentials
- Set up OAuth consent and redirect URLs
- Connect Google Calendar accounts
- Implement and validate automatic calendar synchronization

Manual `.ics` import/export is available as a fallback.

### Notifications

- Implement push notifications or email delivery
- Schedule notification delivery
- Connect the reminder feed to the frontend notification system

### Backend Testing and Deployment

- Run full integration tests
- Verify building coordinates and walking routes
- Validate database migrations
- Confirm correct timezone handling
- Configure production security and CORS
- Add appropriate rate limiting and messaging abuse controls
- Improve routing reliability and caching
- Test all features with real event data

SQLite is currently used for local development. SQLAlchemy's `create_all` does not automatically migrate existing database columns.

## Current Development Status

The backend contains implementations for the major features described in the project portfolio, including event discovery, personal scheduling, travel feasibility, recommendations, calendar files, RSVP, and networking.

These implementations still require full testing and frontend integration before the application can be considered complete.

Google Calendar synchronization and push notifications remain unfinished.

## Team Responsibilities

**Backend:** API development, event importing, scheduling logic, routing, recommendations, database functionality, and backend testing.

**Frontend:** React Native interface, campus map, event discovery screens, daily timeline, conflict visualization, and integration with backend endpoints.

**Google Calendar Integration:** Google Cloud configuration, OAuth, calendar synchronization, and related integration testing.

The team will collaborate on end-to-end testing, bug fixes, and preparation for the final demonstration.
