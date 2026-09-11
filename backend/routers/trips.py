"""Trips router – CRUD for saved trips."""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.db.database import get_db
from backend.models.trip import Trip
from backend.models.schemas import TripOut

router = APIRouter()


@router.get("/get-trips/{user_id}", response_model=list[TripOut])
async def get_trips(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Trip)
        .where(Trip.user_id == user_id)
        .options(selectinload(Trip.items))
        .order_by(Trip.created_at.desc())
    )
    return result.scalars().all()


@router.get("/trips/{trip_id}", response_model=TripOut)
async def get_trip(trip_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Trip).where(Trip.id == trip_id).options(selectinload(Trip.items))
    )
    trip = result.scalar_one_or_none()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip


@router.delete("/trips/{trip_id}", status_code=204)
async def delete_trip(trip_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Trip).where(Trip.id == trip_id))
    trip = result.scalar_one_or_none()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    await db.delete(trip)


@router.post("/save-trip")
async def save_trip_alias():
    """Alias endpoint – saving happens automatically in /generate-itinerary."""
    return {"message": "Trips are auto-saved during generation. Use GET /get-trips/{user_id} to retrieve them."}
