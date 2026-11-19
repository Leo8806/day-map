from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    ConfigDict,
    model_validator,
)


# --------------------------------------------------
# User Registration
# --------------------------------------------------

class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8)


# --------------------------------------------------
# User Authentication
# --------------------------------------------------

class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# --------------------------------------------------
# User Profiles
# --------------------------------------------------

class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    is_admin: bool
    interests: str

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100
    )

    interests: str | None = Field(
        default=None,
        max_length=500
    )


# --------------------------------------------------
# Event Creation
# --------------------------------------------------

class EventCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)
    location: str = Field(min_length=1, max_length=200)
    start_time: datetime
    end_time: datetime
    category: str = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def validate_times(self):
        if (
            self.start_time.tzinfo is None
            or self.end_time.tzinfo is None
        ):
            raise ValueError(
                "Event times must include a timezone"
            )

        if self.end_time <= self.start_time:
            raise ValueError(
                "End time must be after start time"
            )

        return self


# --------------------------------------------------
# Event Responses
# --------------------------------------------------

class EventResponse(BaseModel):
    id: int
    title: str
    description: str
    location: str
    start_time: datetime
    end_time: datetime
    category: str
    created_by: int
    status: Literal[
        "pending",
        "approved",
        "rejected"
    ]

    model_config = ConfigDict(from_attributes=True)
