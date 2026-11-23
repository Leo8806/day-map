"""Run with: python -m unittest discover -s tests -v (from backend/)."""
import unittest
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from models import Base, User, Event, CalendarCommitment, ScheduledEvent, SavedEvent
from routers.discovery import free_time, rank, reminders, alternatives, swap_event, SwapInput
from fastapi import HTTPException


class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.user = User(name='Test', email='test@example.org', password_hash='not-used', interests='Research')
        self.db.add(self.user); self.db.commit()
        self.now = datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)

    def tearDown(self):
        self.db.close(); self.engine.dispose()

    def event(self, title, start, end, category='Research'):
        e = Event(title=title, description='Test', location='Unknown building',
                  start_time=start, end_time=end, category=category,
                  created_by=self.user.id, status='approved')
        self.db.add(e); self.db.commit()
        return e

    def test_free_time_excludes_commitments(self):
        begin = self.now + timedelta(days=1)
        self.db.add(CalendarCommitment(user_id=self.user.id, title='Class', location='',
                     start_time=begin+timedelta(hours=1), end_time=begin+timedelta(hours=2)))
        self.db.commit()
        gaps = free_time(begin.replace(tzinfo=timezone.utc),
                         (begin+timedelta(hours=3)).replace(tzinfo=timezone.utc),
                         15, self.user, self.db)
        self.assertEqual([x['minutes'] for x in gaps], [60, 60])

    def test_rank_interest_and_unknown(self):
        begin = self.now + timedelta(days=1)
        research = self.event('Research', begin, begin+timedelta(minutes=30))
        career = self.event('Career', begin+timedelta(hours=1), begin+timedelta(hours=2), 'Career')
        rows = rank([career, research], self.user, self.db, [], True)
        self.assertEqual(rows[0]['event_id'], research.id)
        self.assertEqual(rows[0]['feasibility'], 'fits')

    def test_overlapping_alternative_excluded(self):
        begin = self.now + timedelta(days=1)
        original = self.event('Original', begin, begin+timedelta(hours=1))
        bad = self.event('Overlap', begin, begin+timedelta(hours=1))
        self.db.add(CalendarCommitment(user_id=self.user.id, title='Class', location='',
                     start_time=begin, end_time=begin+timedelta(hours=1)))
        self.db.commit()
        rows = alternatives(original.id, 10, self.user, self.db)
        self.assertFalse(any(x['event_id'] == bad.id for x in rows))

    def test_reminders_only_own_events(self):
        soon = self.now + timedelta(minutes=20)
        saved = self.event('Saved', soon, soon+timedelta(minutes=30))
        other = self.event('Other', soon, soon+timedelta(minutes=30))
        self.db.add(SavedEvent(user_id=self.user.id, event_id=saved.id)); self.db.commit()
        rows = reminders(60, self.user, self.db)
        self.assertEqual([r['event_id'] for r in rows], [saved.id])

    def test_swap_atomic_and_override(self):
        begin = self.now + timedelta(days=1)
        original = self.event('Original', begin, begin+timedelta(hours=1))
        replacement = self.event('Replacement', begin+timedelta(hours=2), begin+timedelta(hours=3))
        self.db.add(ScheduledEvent(user_id=self.user.id, event_id=original.id)); self.db.commit()
        result = swap_event(original.id, SwapInput(replacement_event_id=replacement.id), self.user, self.db)
        self.assertEqual(result['added_event_id'], replacement.id)
        self.assertEqual([r.event_id for r in self.db.query(ScheduledEvent).all()], [replacement.id])


if __name__ == '__main__':
    unittest.main()
