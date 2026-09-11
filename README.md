# ✈️ Travel Planner Agent

An AI-powered full-stack travel planning web application that uses **IBM Granite** (via watsonx.ai) and **RAG (Retrieval-Augmented Generation)** to build accurate, grounded day-by-day travel itineraries.

---

## Architecture Overview

```
Travel Planner Agent/
├── frontend/           # React (Vite) – UI
│   └── src/
│       ├── pages/      # PlannerPage, TripsPage, TripDetailPage, LoginPage
│       ├── components/ # ItineraryDisplay, DayCard
│       ├── hooks/      # useUser (context)
│       └── api/        # Axios client
├── backend/            # FastAPI – REST API
│   ├── routers/        # itinerary, trips, users, weather
│   ├── models/         # SQLAlchemy ORM + Pydantic schemas
│   ├── services/       # llm_service (Granite + IAM), weather_service
│   ├── db/             # Async SQLAlchemy engine
│   └── config.py       # Settings from .env
├── rag/
│   ├── retriever.py          # ChromaDB query + embedding lookup
│   ├── seed_knowledge_base.py # One-time seeding script
│   └── data/destinations/    # JSON knowledge base files
├── schema.sql          # MySQL schema (run once)
├── requirements.txt
└── .env.example
```

---

## Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.11+ |
| Node.js | 18+ |
| MySQL | 8.0+ |
| Git | any |

---

## 1. Clone & Configure

```bash
git clone <repo-url>
cd "Travel Planner Agent"

# Copy and fill in your environment file
cp .env.example .env
```

Edit `.env` with your values:

```env
# MySQL
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=travel_planner

# IBM watsonx (see Section 4)
IBM_API_KEY=your_ibm_api_key
IBM_PROJECT_ID=your_project_id
IBM_MODEL_ID=ibm/granite-4-h-small
IBM_URL=https://us-south.ml.cloud.ibm.com/ml/v1/text/generation?version=2023-05-29

# Optional: OpenWeatherMap
OPENWEATHER_API_KEY=your_key_here
```

---

## 2. Database Setup

```bash
# Create the schema
mysql -u root -p < schema.sql
```

> SQLAlchemy will also auto-create tables on first startup via `init_db()`.

---

## 3. Backend Setup

```bash
# Create a Python virtual environment
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Seed the RAG knowledge base (first time only)
python -m rag.seed_knowledge_base

# Start the API server
uvicorn backend.main:app --reload --port 8000
```

API docs available at: **http://localhost:8000/docs**

---

## 4. IBM Cloud Lite / Granite Configuration

### Getting Your Credentials

1. Go to [IBM Cloud](https://cloud.ibm.com) → Create a free **Lite** account
2. Navigate to **watsonx.ai** → Create a project
3. Copy your **Project ID** from the project settings
4. Go to **Manage → Access (IAM) → API Keys** → Create an API key
5. The model endpoint and model ID are pre-configured in `.env.example`

### How It Works

The backend uses IBM's IAM token service to exchange your API key for a short-lived bearer token, then calls the Granite inference endpoint with your prompt. Tokens are cached for their full lifetime (~1 hour) and refreshed automatically.

```
IBM API Key → IAM Token Service → Bearer Token → Granite Endpoint
```

### Rate Limits & Retries

The `llm_service.py` handles HTTP 429 (Too Many Requests) with exponential backoff. The default config is 3 retries with 2-second base delay. Configure via `LLM_MAX_RETRIES` and `LLM_RETRY_DELAY` in `.env`.

---

## 5. RAG Knowledge Base

### Seeding

```bash
python -m rag.seed_knowledge_base
```

This reads all `.json` files in `rag/data/destinations/`, chunks them, generates embeddings with `all-MiniLM-L6-v2` (runs locally, no API required), and stores them in ChromaDB at `rag/embeddings/chroma_db/`.

### Pre-seeded Destinations (10)

| Destination | Highlights |
|-------------|-----------|
| Paris, France | Art, culture, food, romance |
| Tokyo, Japan | Technology, food, culture, adventure |
| Kyoto, Japan | Temples, history, traditional Japan |
| Bali, Indonesia | Nature, surfing, spirituality, beach |
| Barcelona, Spain | Architecture, food, nightlife, beach |
| New York City, USA | Culture, food, art, entertainment |
| Cape Town, South Africa | Wildlife, nature, wine, adventure |
| Santorini, Greece | Romance, beach, wine, photography |
| Marrakech, Morocco | Culture, food, souks, architecture |
| Patagonia, Argentina/Chile | Hiking, glaciers, wildlife, adventure |

### Adding More Destinations

Create a new JSON file in `rag/data/destinations/` following this schema:

```json
{
  "title": "Destination Name, Country",
  "destination": "City Name",
  "overview": "...",
  "best_time_to_visit": "...",
  "climate": "...",
  "attractions": [
    {"name": "...", "description": "...", "estimated_cost_usd": 0}
  ],
  "food": [{"name": "...", "description": "...", "avg_cost_usd": 0}],
  "accommodation": [{"name": "...", "type": "...", "avg_price_usd": 0}],
  "transport": "...",
  "budget_guide": {"budget_per_day_usd": {"low": 0, "mid": 0, "high": 0}},
  "tips": ["..."],
  "interests": ["culture", "food", "adventure"]
}
```

Then re-run the seed script.

---

## 6. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend available at: **http://localhost:3000**

> The Vite dev server proxies all `/api/*` requests to `http://localhost:8000`.

---

## 7. API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/users` | Create a new user |
| `GET` | `/api/users/{id}` | Get user by ID |
| `POST` | `/api/generate-itinerary` | Generate AI itinerary (RAG + Granite) |
| `POST` | `/api/refine-itinerary` | Chat-style refinement of existing trip |
| `GET` | `/api/get-trips/{user_id}` | List all saved trips for a user |
| `GET` | `/api/trips/{id}` | Get single trip with all itinerary items |
| `DELETE` | `/api/trips/{id}` | Delete a trip |
| `GET` | `/api/weather` | Get weather forecast for city/dates |

### Example: Generate Itinerary

```bash
curl -X POST http://localhost:8000/api/generate-itinerary \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "destination": "Tokyo",
    "start_date": "2025-04-01",
    "end_date": "2025-04-05",
    "budget_min": 1500,
    "budget_max": 3000,
    "num_travelers": 2,
    "interests": ["Food", "Culture", "Adventure"],
    "save": true
  }'
```

### Example: Refine Itinerary

```bash
curl -X POST http://localhost:8000/api/refine-itinerary \
  -H "Content-Type: application/json" \
  -d '{"trip_id": 1, "user_message": "Make day 2 less crowded and add more food stops"}'
```

---

## 8. System Prompt Design

The Granite LLM is constrained via a structured system prompt that:

1. **Limits hallucination** – instructions say "NEVER invent attractions not mentioned in context"
2. **Enforces JSON output** – the model is shown the exact output schema and must follow it
3. **Grounds in RAG context** – retrieved destination docs are injected into the user message
4. **Weather awareness** – forecast data is included; outdoor activities flagged `weather_risk: "high"` when rain is forecast

---

## 9. Optional: OpenWeatherMap Integration

1. Register at [openweathermap.org](https://openweathermap.org/api) (free tier available)
2. Add your key to `.env`: `OPENWEATHER_API_KEY=your_key`
3. Forecasts are automatically included in itinerary generation and outdoor activities are flagged

Without an API key, weather features are silently disabled and the agent still works normally.

---

## 10. Development Notes

- **Backend hot-reload**: `uvicorn backend.main:app --reload`
- **Re-seed RAG**: `python -m rag.seed_knowledge_base` (drops and recreates the collection)
- **MySQL schema reset**: `mysql -u root -p < schema.sql`
- **API interactive docs**: http://localhost:8000/docs (Swagger UI)
- **Environment**: all config lives in `.env` – never hardcode secrets

---

## License

MIT
