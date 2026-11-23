import re
import time
from datetime import datetime
from urllib.parse import urljoin, urlparse
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup
from sqlalchemy import select

from database import SessionLocal
from models import Event, User

import json
import html

# --------------------------------------------------
# Penn Engineering Configuration
# --------------------------------------------------

BASE_URL = "https://events.engineering.upenn.edu/"
SOURCE = "penn_engineering"
TIMEZONE = ZoneInfo("America/New_York")

HEADERS = {
    "User-Agent": "DayMapStudentProject/1.0"
}


# --------------------------------------------------
# Fetch Website Content
# --------------------------------------------------

def fetch_page(url):
    response = requests.get(
        url,
        headers=HEADERS,
        timeout=15
    )

    response.raise_for_status()

    return BeautifulSoup(
        response.text,
        "html.parser"
    )


# --------------------------------------------------
# Find Individual Event Links
# --------------------------------------------------


def get_event_links(max_pages=20):
    links = set()

    for page_number in range(1, max_pages + 1):

        # Penn Engineering's paginated calendar
        if page_number == 1:
            url = BASE_URL + "calendar/list/"
        else:
            url = (
                BASE_URL
                + f"calendar/list/page/{page_number}/"
            )

        print(f"Checking calendar page {page_number}...")

        try:
            soup = fetch_page(url)
        except requests.RequestException as error:
            print(f"Could not fetch {url}: {error}")
            break

        # Find links to individual event pages
        page_links = set()

        for anchor in soup.select('a[href]'):
            event_url = urljoin(
                url,
                anchor["href"]
            )

            parsed = urlparse(event_url)

            if (
                parsed.netloc == "events.engineering.upenn.edu"
                and parsed.path.startswith("/event/")
                and parsed.path.strip("/") != "event"
            ):
                page_links.add(
                    event_url.split("?")[0].rstrip("/") + "/"
                )

        # Stop when a page contains no events
        if not page_links:
            break

        # Stop if this page has no new events
        new_links = page_links - links

        if not new_links:
            break

        links.update(new_links)

        print(
            f"Found {len(new_links)} new event links "
            f"({len(links)} total)"
        )

        # Avoid sending requests too quickly
        time.sleep(1)

    return sorted(links)

# --------------------------------------------------
# Parse an Individual Event
# --------------------------------------------------


def parse_event(url):
    soup = fetch_page(url)

    # Find structured event data
    for script in soup.select(
        'script[type="application/ld+json"]'
    ):
        try:
            data = json.loads(script.get_text())
        except json.JSONDecodeError:
            continue

        # JSON-LD can contain a list of objects
        if isinstance(data, dict):
            data = [data]

        for item in data:
            if item.get("@type") != "Event":
                continue

            # Event title
            title = html.unescape(
                item.get("name", "")
            ).strip()


            # --------------------------------------------------
            # Event Description
            # --------------------------------------------------

            # Use JSON-LD as a fallback
            raw_description = html.unescape(
                item.get("description", "")
            )

            description = BeautifulSoup(
                raw_description,
                "html.parser"
            ).get_text(" ", strip=True)

            # Try to extract the full description
            # from the event page
            description_container = soup.select_one(
                "article div.col-12.col-lg-8.offset-lg-3"
            )

            if description_container:
                paragraphs = description_container.find_all(
                    "p"
                )

                full_description = " ".join(
                    paragraph.get_text(" ", strip=True)
                    for paragraph in paragraphs
                )

                if full_description:
                    description = full_description


            # Event dates
            start = datetime.fromisoformat(
                item["startDate"]
            )

            end = datetime.fromisoformat(
                item["endDate"]
            )

            # Event location
            location_data = item.get("location", {})

            if isinstance(location_data, dict):
                location = location_data.get(
                    "name",
                    "Penn Engineering"
                )
            else:
                location = "Penn Engineering"

            return {
                "title": title[:200],
                "description": description or title,
                "location": location[:200],
                "start_time": start,
                "end_time": end,
                "category": "Engineering",
                "source": SOURCE,
                "source_url": url,
                "external_id": urlparse(url).path.strip("/"),
            }

    return None

# --------------------------------------------------
# Import Events into SQLite
# --------------------------------------------------

def import_penn_events():
    links = get_event_links()

    imported = 0
    updated = 0
    skipped = 0

    with SessionLocal() as db:
        # Find an administrator to own imported events
        admin = db.scalar(
            select(User).where(
                User.is_admin.is_(True)
            )
        )

        if admin is None:
            raise RuntimeError(
                "No administrator account found."
            )

        for url in links:
            try:
                event_data = parse_event(url)

                if event_data is None:
                    skipped += 1
                    continue

                # Convert Penn's event times to UTC
                start_time = event_data[
                    "start_time"
                ].astimezone(
                    ZoneInfo("UTC")
                ).replace(tzinfo=None)

                end_time = event_data[
                    "end_time"
                ].astimezone(
                    ZoneInfo("UTC")
                ).replace(tzinfo=None)

                # Check whether the event already exists
                existing = db.scalar(
                    select(Event).where(
                        Event.source == SOURCE,
                        Event.external_id
                        == event_data["external_id"]
                    )
                )

                if existing:
                    # Update the event's latest information
                    existing.title = event_data["title"]
                    existing.description = event_data["description"]
                    existing.location = event_data["location"]
                    existing.start_time = start_time
                    existing.end_time = end_time
                    existing.category = event_data["category"]
                    existing.source_url = event_data["source_url"]

                    updated += 1

                else:
                    # Create a new imported event
                    event = Event(
                        title=event_data["title"],
                        description=event_data["description"],
                        location=event_data["location"],
                        start_time=start_time,
                        end_time=end_time,
                        category=event_data["category"],
                        source=event_data["source"],
                        source_url=event_data["source_url"],
                        external_id=event_data["external_id"],
                        created_by=admin.id,
                        status="approved"
                    )

                    db.add(event)
                    imported += 1

                db.commit()

            except Exception as error:
                db.rollback()
                print(f"Failed to import {url}: {error}")
                skipped += 1

    return {
        "imported": imported,
        "updated": updated,
        "skipped": skipped
    }

# --------------------------------------------------
# Run Importer Manually
# --------------------------------------------------

if __name__ == "__main__":
    print(import_penn_events())
