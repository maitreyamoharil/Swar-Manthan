
import os
from uuid import UUID

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_API_KEY = os.getenv("SUPABASE_API_KEY", "")

if not SUPABASE_URL or not SUPABASE_API_KEY:
    raise RuntimeError("Missing Supabase environment variables")

REST_URL = f"{SUPABASE_URL}/rest/v1"

HEADERS = {
    "apikey": SUPABASE_API_KEY,
    "Authorization": f"Bearer {SUPABASE_API_KEY}",
    "Content-Type": "application/json",
}

app = FastAPI(title="Swar-Manthan API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://swarmanthan.vercel.app",
        "http://localhost:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


async def supabase_request(url, method="GET", params=None, body=None):
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.request(
                method,
                url,
                headers=HEADERS,
                params=params,
                json=body,
            )

        if response.is_error:
            raise HTTPException(
                status_code=response.status_code,
                detail=response.text,
            )

        if response.status_code == 204 or not response.content:
            return None

        return response.json()

    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Could not connect to Supabase: {str(exc)}",
        )


@app.get("/")
def home():
    return {"message": "Swar-Manthan API is running"}

# 1. GET ALL EVENTS
@app.get("/api/events")
async def get_all_events():
    return await supabase_request(
        f"{REST_URL}/Events",
        params={
            "select": "*",
            "order": "Date.asc",
        },
    )


# 2. GET INDIVIDUAL EVENT BY UUID
@app.get("/api/events/{event_id}")
async def get_event_by_id(event_id: UUID):
    rows = await supabase_request(
        f"{REST_URL}/Events",
        params={
            "select": "*",
            "ID": f"eq.{event_id}",
        },
    )

    if not rows:
        raise HTTPException(status_code=404, detail="Event not found")

    return rows[0]


# 4. GET ALL JOURNEY
@app.get("/api/journey")
async def get_all_journey():
    return await supabase_request(
        f"{REST_URL}/Journey",
        params={
            "select": "*",
            "order": "Date.asc",
        },
    )


# 5. GET INDIVIDUAL JOURNEY BY UUID
@app.get("/api/journey/{journey_id}")
async def get_journey_by_id(journey_id: UUID):
    rows = await supabase_request(
        f"{REST_URL}/Journey",
        params={
            "select": "*",
            "ID": f"eq.{journey_id}",
        },
    )

    if not rows:
        raise HTTPException(
            status_code=404,
            detail="Journey record not found",
        )

    return rows[0]


# 6. GET ALL TEAM
@app.get("/api/team")
async def get_all_team():
    return await supabase_request(
        f"{REST_URL}/Team",
        params={
            "select": "*",
            "order": "Created_At.asc",
        },
    )


# 7. GET ALL VIDEOS
@app.get("/api/videos")
async def get_all_videos():
    return await supabase_request(
        f"{REST_URL}/Videos",
        params={
            "select": "*",
            "order": "Created_At.desc",
        },
    )
