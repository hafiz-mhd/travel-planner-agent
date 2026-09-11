"""Pydantic request/response schemas."""
from __future__ import annotations
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator


# ── User ──────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email: EmailStr
    name: str
    preferences: Optional[str] = None


class UserOut(BaseModel):
    id: int
    email: str
    name: str
    preferences: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Itinerary ─────────────────────────────────────────────────────────────────

class ItineraryItemOut(BaseModel):
    day_number: int
    period: str
    activity: str
    location: Optional[str]
    description: Optional[str]
    estimated_cost: Optional[float]
    weather_risk: Optional[str]
    tips: Optional[str]

    model_config = {"from_attributes": True}


# ── Trip ──────────────────────────────────────────────────────────────────────

class TripCreate(BaseModel):
    user_id: int
    destination: str
    start_date: date
    end_date: date
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    num_travelers: int = 1
    interests: Optional[str] = None

    @field_validator("end_date")
    @classmethod
    def end_after_start(cls, v, info):
        if "start_date" in info.data and v < info.data["start_date"]:
            raise ValueError("end_date must be after start_date")
        return v


class TripOut(BaseModel):
    id: int
    user_id: int
    title: str
    destination: str
    start_date: date
    end_date: date
    budget_min: Optional[float]
    budget_max: Optional[float]
    num_travelers: int
    interests: Optional[str]
    created_at: datetime
    items: list[ItineraryItemOut] = []

    model_config = {"from_attributes": True}


# ── Generate/Refine ───────────────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    user_id: int
    destination: str          # or "surprise me"
    start_date: date
    end_date: date
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    num_travelers: int = 1
    interests: list[str] = []
    save: bool = True          # whether to persist after generation


class RefineRequest(BaseModel):
    trip_id: int
    user_message: str          # "make day 2 less crowded", etc.


class GenerateResponse(BaseModel):
    trip_id: Optional[int]
    itinerary: list[dict]      # raw day objects from LLM
    title: Optional[str] = None
    summary: Optional[str] = None
    weather_summary: Optional[str] = None
    sources: list[str] = []    # destination doc titles used as RAG context
