"""Itinerary router – generate and refine trip itineraries."""
from __future__ import annotations
import json
import logging
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.db.database import get_db
from backend.models.trip import Trip, ItineraryItem
from backend.models.schemas import GenerateRequest, RefineRequest, GenerateResponse
from backend.services.llm_service import call_granite
from backend.services.weather_service import get_weather_forecast
from rag.retriever import retrieve_context

logger = logging.getLogger(__name__)
router = APIRouter()


def _build_generate_prompt(req: GenerateRequest, context: str, weather: str) -> str:
    num_days = (req.end_date - req.start_date).days + 1
    budget_str = (
        f"INR {int(req.budget_min):,} to INR {int(req.budget_max):,} total trip budget"
        if req.budget_min and req.budget_max
        else "budget flexible (provide reasonable INR estimates per person)"
    )
    interests = ", ".join(req.interests) if req.interests else "general tourism"
    destination = req.destination if req.destination.lower() != "surprise me" else "a surprise destination chosen from the context below"

    return f"""Plan a {num_days}-day trip to {destination}.
Travelers: {req.num_travelers}
Dates: {req.start_date} to {req.end_date}
Budget: {budget_str}
Interests: {interests}

IMPORTANT: ALL estimated_cost values MUST be in Indian Rupees (INR) per person.
Do NOT use USD or any other currency. Use only plain ASCII text in descriptions.

WEATHER FORECAST:
{weather}

DESTINATION KNOWLEDGE BASE (use ONLY this for specific recommendations):
{context}

Create a complete day-by-day itinerary following the JSON format exactly.
Fill in morning, afternoon, and evening for every single day.
Mark any outdoor activity as weather_risk: "high" if rain is likely on that day."""


def _build_refine_prompt(existing_itinerary: str, user_message: str, context: str) -> str:
    return f"""Here is the current itinerary (JSON):
{existing_itinerary}

The traveler wants to refine it with this request:
"{user_message}"

DESTINATION KNOWLEDGE BASE:
{context}

IMPORTANT: ALL estimated_cost values must remain in Indian Rupees (INR) per person.
Use only plain ASCII text. Return the COMPLETE updated itinerary JSON with the requested changes applied.
Keep all unmentioned days exactly as they were. Output JSON only — no extra text."""


@router.post("/generate-itinerary", response_model=GenerateResponse)
async def generate_itinerary(req: GenerateRequest, db: AsyncSession = Depends(get_db)):
    # 1. RAG retrieval
    context_docs, sources = retrieve_context(req.destination, req.interests)

    # 2. Weather
    weather_data = await get_weather_forecast(req.destination, req.start_date, req.end_date)
    weather_text = weather_data["summary"]
    if weather_data["days"]:
        for day in weather_data["days"]:
            rain_flag = " ⚠ Rain likely" if day["rain_likely"] else ""
            weather_text += f"\n  {day['date']}: {day['avg_temp_c']}°C – {', '.join(set(day['conditions']))}{rain_flag}"

    # 3. Build prompt and call Granite
    prompt = _build_generate_prompt(req, context_docs, weather_text)
    try:
        itinerary_json = await call_granite(prompt)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    # LLM sometimes returns just a list or a dict without the top-level wrapper
    if isinstance(itinerary_json, list):
        itinerary_json = {"days": itinerary_json}
    days_list: list[dict] = itinerary_json.get("days", [])

    # Synthesise title/summary if LLM omitted, left empty, or returned null
    num_days = (req.end_date - req.start_date).days + 1
    raw_title = (itinerary_json.get("title") or "").strip()
    raw_summary = (itinerary_json.get("summary") or "").strip()
    if not raw_title:
        dest = req.destination if req.destination.lower() != "surprise me" else (
            (days_list[0].get("morning") or {}).get("location", "Mystery Destination") if days_list else "Mystery Destination"
        )
        itinerary_json["title"] = f"{num_days}-Day Trip to {dest.title()}"
    if not raw_summary:
        interests_str = " and ".join(req.interests[:2]) if req.interests else "sightseeing"
        itinerary_json["summary"] = (
            f"Your {num_days}-day itinerary covers {interests_str} "
            f"across {req.destination}. Activities are planned for each morning, afternoon, and evening."
        )

    trip_id: int | None = None

    # 4. Persist if requested
    if req.save:
        trip = Trip(
            user_id=req.user_id,
            title=itinerary_json.get("title", f"Trip to {req.destination}"),
            destination=req.destination,
            start_date=req.start_date,
            end_date=req.end_date,
            budget_min=req.budget_min,
            budget_max=req.budget_max,
            num_travelers=req.num_travelers,
            interests=", ".join(req.interests),
            raw_itinerary=json.dumps(itinerary_json),
        )
        db.add(trip)
        await db.flush()

        for day_data in days_list:
            day_num = day_data.get("day", 0)
            # Weather risk lookup for this day
            weather_day = next(
                (d for d in weather_data["days"] if d["date"] == day_data.get("date")), None
            )
            rain_likely = weather_day["rain_likely"] if weather_day else False

            for period in ("morning", "afternoon", "evening"):
                slot = day_data.get(period, {})
                if not slot:
                    continue
                item = ItineraryItem(
                    trip_id=trip.id,
                    day_number=day_num,
                    period=period,
                    activity=slot.get("activity", ""),
                    location=slot.get("location"),
                    description=slot.get("description"),
                    estimated_cost=slot.get("estimated_cost"),
                    weather_risk="high" if rain_likely and period != "evening" else slot.get("weather_risk", "low"),
                    tips=slot.get("tips"),
                )
                db.add(item)

        trip_id = trip.id

    return GenerateResponse(
        trip_id=trip_id,
        itinerary=days_list,
        title=itinerary_json.get("title"),
        summary=itinerary_json.get("summary"),
        weather_summary=weather_data["summary"],
        sources=sources,
    )


@router.post("/refine-itinerary", response_model=GenerateResponse)
async def refine_itinerary(req: RefineRequest, db: AsyncSession = Depends(get_db)):
    # Load existing trip
    result = await db.execute(select(Trip).where(Trip.id == req.trip_id))
    trip = result.scalar_one_or_none()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    context_docs, sources = retrieve_context(trip.destination, [])
    prompt = _build_refine_prompt(trip.raw_itinerary or "{}", req.user_message, context_docs)

    try:
        updated_json = await call_granite(prompt)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    # Normalise LLM output
    if isinstance(updated_json, list):
        updated_json = {"days": updated_json}
    if not (updated_json.get("title") or "").strip():
        updated_json["title"] = trip.title
    if not (updated_json.get("summary") or "").strip():
        updated_json["summary"] = f"Refined itinerary for {trip.destination}."

    # Update stored itinerary
    trip.raw_itinerary = json.dumps(updated_json)

    # Delete old items and re-insert
    for item in list(trip.items):
        await db.delete(item)
    await db.flush()

    for day_data in updated_json.get("days", []):
        for period in ("morning", "afternoon", "evening"):
            slot = day_data.get(period, {})
            if not slot:
                continue
            db.add(ItineraryItem(
                trip_id=trip.id,
                day_number=day_data.get("day", 0),
                period=period,
                activity=slot.get("activity", ""),
                location=slot.get("location"),
                description=slot.get("description"),
                estimated_cost=slot.get("estimated_cost"),
                weather_risk=slot.get("weather_risk", "low"),
                tips=slot.get("tips"),
            ))

    return GenerateResponse(
        trip_id=trip.id,
        itinerary=updated_json.get("days", []),
        title=updated_json.get("title"),
        summary=updated_json.get("summary"),
        weather_summary=None,
        sources=sources,
    )
