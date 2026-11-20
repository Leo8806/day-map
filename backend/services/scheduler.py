
from apscheduler.schedulers.background import BackgroundScheduler

from services.penn_events import import_penn_events


# --------------------------------------------------
# Automatic Penn Engineering Event Imports
# --------------------------------------------------

scheduler = BackgroundScheduler(timezone="UTC")


def refresh_penn_events():
    """Fetch and synchronize Penn Engineering events."""

    print("Starting automatic Penn Engineering import...")

    try:
        result = import_penn_events()
        print(f"Penn Engineering import complete: {result}")

    except Exception as error:
        print(f"Penn Engineering import failed: {error}")


def start_scheduler():
    """Start periodic event synchronization."""

    if scheduler.running:
        return

    scheduler.add_job(
        refresh_penn_events,
        trigger="interval",
        hours=6,
        id="penn_engineering_import",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    scheduler.start()
    print("Event scheduler started (every 6 hours).")


def stop_scheduler():
    """Stop the scheduler when the application shuts down."""

    if scheduler.running:
        scheduler.shutdown(wait=False)
        print("Event scheduler stopped.")
