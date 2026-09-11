"""Weather router – expose forecast endpoint to the frontend."""
from __future__ import annotations
from datetime import date
from fastapi import APIRouter
from backend.services.weather_service import get_weather_forecast

router = APIRouter()


@router.get("/weather")
async def weather(city: str, start_date: date, end_date: date):
    return await get_weather_forecast(city, start_date, end_date)
