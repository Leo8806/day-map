"""Fill the three missing Penn building records.

Run from backend/: python -m services.seed_missing_buildings --preview
                   python -m services.seed_missing_buildings --apply
The first two coordinates are approximate campus map points and should be
visually reviewed; Singh is resolved from its exact street address via Nominatim.
"""
import argparse
import os
import requests
from sqlalchemy import select
from database import Base, engine, SessionLocal
from models import Building

BUILDINGS = [
    {"name": "Huntsman Hall", "address": "3730 Walnut Street, Philadelphia, PA 19104, USA", "latitude": 39.9529106, "longitude": -75.1982674},
    {"name": "David Rittenhouse Laboratory", "address": "209 South 33rd Street, Philadelphia, PA 19104, USA", "latitude": 39.95208, "longitude": -75.18920},
]
SINGH_NAME = "Singh Center for Nanotechnology"
SINGH_ADDRESS = "3205 Walnut Street, Philadelphia, PA 19104, USA"


def locate_singh():
    response = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={"street": "3205 Walnut Street", "city": "Philadelphia", "state": "Pennsylvania", "postalcode": "19104", "country": "USA", "format": "json", "limit": 5},
        headers={"User-Agent": "DayMapUniversityProject/0.2 (" + os.getenv("DAYMAP_GEOCODER_CONTACT", "student project") + ")"},
        timeout=15,
    )
    response.raise_for_status()
    for item in response.json():
        lat, lon = float(item["lat"]), float(item["lon"])
        if 39.949 < lat < 39.955 and -75.195 < lon < -75.185:
            return {"name": SINGH_NAME, "address": SINGH_ADDRESS, "latitude": lat, "longitude": lon}
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Write to local SQLite DB")
    parser.add_argument("--preview", action="store_true", help="Print candidates only (default)")
    parser.add_argument("--update-existing", action="store_true", help="Replace existing points when applying")
    args = parser.parse_args()
    candidates = list(BUILDINGS)
    try:
        singh = locate_singh()
    except requests.RequestException as exc:
        print(f"Singh Center: address lookup failed ({exc})")
        singh = None
    if singh:
        candidates.append(singh)
    else:
        print(f"Singh Center: NOT FOUND at {SINGH_ADDRESS}. No coordinate will be guessed or saved.")
    for b in candidates:
        print(f'{b["name"]}: {b["latitude"]:.7f}, {b["longitude"]:.7f} | {b["address"]}')
    if not args.apply:
        print("Preview only. Verify map points before running --apply.")
        return
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        for b in candidates:
            existing = db.scalar(select(Building).where(Building.name == b["name"]))
            if existing and not args.update_existing:
                print(f'SKIPPED {b["name"]}: already present (use --update-existing if needed)')
                continue
            if existing:
                existing.address, existing.latitude, existing.longitude = b["address"], b["latitude"], b["longitude"]
            else:
                db.add(Building(**b))
            db.commit()
            print(f'SAVED {b["name"]}')
    print("Check GET /buildings for saved locations.")


if __name__ == "__main__":
    main()
