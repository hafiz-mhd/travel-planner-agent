"""Travel Planner Agent – FastAPI entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.db.database import init_db
from backend.routers import itinerary, trips, users, weather


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="Travel Planner Agent API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(itinerary.router, prefix="/api", tags=["itinerary"])
app.include_router(trips.router, prefix="/api", tags=["trips"])
app.include_router(users.router, prefix="/api", tags=["users"])
app.include_router(weather.router, prefix="/api", tags=["weather"])


@app.get("/health")
async def health():
    return {"status": "ok", "service": "travel-planner-agent"}
