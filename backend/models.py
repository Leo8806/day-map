
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
