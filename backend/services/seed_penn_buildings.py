"""Import verified-by-geocoder Penn campus building points, with manual review before use.

Run from backend/: python -m services.seed_penn_buildings --preview
Then: python -m services.seed_penn_buildings --apply
Geocoding requires internet; verify results manually. Nominatim usage: <=1 request/sec, identifying User-Agent.
"""
import argparse
import os
import time
import requests
from sqlalchemy import select
from database import Base, engine, SessionLocal
from models import Building

NAMES = [
    'Houston Hall', 'Huntsman Hall', 'Van Pelt Library', 'Levine Hall',
    'Towne Building', 'College Hall', 'Fisher Fine Arts Library',
    'Williams Hall', 'David Rittenhouse Laboratory', 'Singh Center for Nanotechnology',
    'Penn Museum', 'Meyerson Hall', 'Hill College House', 'Annenberg Center',
]

def lookup(name: str):
    response = requests.get('https://nominatim.openstreetmap.org/search', params={
        'q': f'{name}, University of Pennsylvania, Philadelphia, PA, USA',
        'format': 'json', 'limit': 3, 'addressdetails': 1},
        headers={'User-Agent': f'DayMapUniversityProject/0.1 ({os.getenv("DAYMAP_GEOCODER_CONTACT", "student project")})'}, timeout=12)
    response.raise_for_status()
    for hit in response.json():
        lat, lon = float(hit['lat']), float(hit['lon'])
        # Reject hits outside the campus area; this does NOT establish building identity.
        if 39.93 < lat < 39.97 and -75.22 < lon < -75.17:
            return {'name': name, 'address': hit['display_name'], 'latitude': lat, 'longitude': lon}
    return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true', help='Save geocoded results to local DB')
    parser.add_argument('--preview', action='store_true', help='Preview only (default)')
    args = parser.parse_args()
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        for name in NAMES:
            try:
                result = lookup(name)
                if result:
                    print(f'{name}: {result["latitude"]}, {result["longitude"]} — {result["address"]}')
                    if args.apply:
                        old = db.scalar(select(Building).where(Building.name == name))
                        if old is None:
                            db.add(Building(**result))
                            db.commit()
                else:
                    print(f'{name}: NOT FOUND — enter coordinates manually via admin API')
            except requests.RequestException as exc:
                print(f'{name}: geocoder unavailable ({exc})')
            time.sleep(1.1)
    if not args.apply:
        print('Preview only. Verify building identities, then run --apply to save.')

if __name__ == '__main__':
    main()
