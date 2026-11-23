
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


# --------------------------------------------------
# User Model
# --------------------------------------------------

class User(Base):
    __tablename__ = "users"

    # User Identification
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    # User Information
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False
    )

    # Authentication
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    is_admin: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    # User Preferences
    interests: Mapped[str] = mapped_column(
        String(500),
        default="",
        nullable=False
    )


# --------------------------------------------------
# Event Model
# --------------------------------------------------

class Event(Base):
    __tablename__ = "events"

    # Event Identification
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    # Event Information
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    location: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

    # Event Schedule
    start_time: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False
    )

    end_time: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False
    )

    # Event Category
    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    # Event Ownership
    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    # Event Approval Status
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False
    )

    # External Event Sources
    source: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    source_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    external_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )


# --------------------------------------------------
# Saved Event Model
# --------------------------------------------------

class SavedEvent(Base):
    __tablename__ = "saved_events"

    # Prevent users from saving the same event twice
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "event_id",
            name="uq_saved_event_user_event"
        ),
    )

    # Saved Event Identification
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    # User Who Saved the Event
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    # Event Being Saved
    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id"),
        nullable=False
    )


# Additive tables; existing user/event tables remain unchanged.
class ScheduledEvent(Base):
    __tablename__ = "scheduled_events"
    __table_args__ = (UniqueConstraint("user_id", "event_id", name="uq_schedule_user_event"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), nullable=False)
    conflict_overridden: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class CalendarCommitment(Base):
    __tablename__ = "calendar_commitments"
    __table_args__ = (UniqueConstraint("user_id", "external_id", name="uq_commitment_user_external"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    location: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    source: Mapped[str] = mapped_column(String(30), default="manual", nullable=False)


class Building(Base):
    __tablename__ = "buildings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    address: Mapped[str] = mapped_column(String(300), nullable=False)
    latitude: Mapped[float] = mapped_column(nullable=False)
    longitude: Mapped[float] = mapped_column(nullable=False)


class TravelPreference(Base):
    __tablename__ = "travel_preferences"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    mode: Mapped[str] = mapped_column(String(20), default="walking", nullable=False)
    buffer_minutes: Mapped[int] = mapped_column(Integer, default=5, nullable=False)


class FriendRequest(Base):
    __tablename__ = "friend_requests"
    __table_args__ = (UniqueConstraint("sender_id", "receiver_id", name="uq_friend_request"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    receiver_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)

class GoogleCalendarConnection(Base):
    __tablename__ = "google_calendar_connections"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    refresh_token_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    calendar_id: Mapped[str] = mapped_column(String(255), default="primary", nullable=False)

class PublicProfile(Base):
    __tablename__ = 'public_profiles'
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), primary_key=True)
    major: Mapped[str] = mapped_column(String(120), default='', nullable=False)
    graduation_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bio: Mapped[str] = mapped_column(String(500), default='', nullable=False)
    interests: Mapped[str] = mapped_column(String(500), default='', nullable=False)
    discoverable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

class EventAttendance(Base):
    __tablename__ = 'event_attendance'
    __table_args__ = (UniqueConstraint('user_id', 'event_id', name='uq_attendance_user_event'),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False, index=True)
    event_id: Mapped[int] = mapped_column(ForeignKey('events.id'), nullable=False, index=True)
    visible: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    networking: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

class UserBlock(Base):
    __tablename__ = 'user_blocks'
    __table_args__ = (UniqueConstraint('blocker_id', 'blocked_id', name='uq_block_pair'),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    blocker_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    blocked_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)


class DirectConversation(Base):
    __tablename__ = 'direct_conversations'
    __table_args__ = (UniqueConstraint('user_low_id', 'user_high_id', name='uq_direct_conversation_pair'),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_low_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False, index=True)
    user_high_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class DirectMessage(Base):
    __tablename__ = 'direct_messages'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey('direct_conversations.id'), nullable=False, index=True)
    sender_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    text: Mapped[str] = mapped_column(String(2000), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
