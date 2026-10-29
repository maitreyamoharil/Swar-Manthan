import os
from typing import Optional
from uuid import UUID

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, Field

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_API_KEY = os.getenv("SUPABASE_API_KEY", "")

if not SUPABASE_URL or not SUPABASE_API_KEY:
    raise RuntimeError("Missing Supabase environment variables")

TABLE_URL = f"{SUPABASE_URL}/rest/v1/Data"

STORAGE_BUCKET = "Swar-Manthan%20Bucket"

def add_image_url(record):
    if record and record.get("Image"):
        path = record["Image"].lstrip("/")

        record["Image_URL"] = (
            f"{SUPABASE_URL}/storage/v1/object/public/"
            f"{STORAGE_BUCKET}/{path}"
        )

    return record

app = FastAPI(title="Swar-Manthan API")

HEADERS = {
    "apikey": SUPABASE_API_KEY,
    "Authorization": f"Bearer {SUPABASE_API_KEY}",
    "Content-Type": "application/json",
}


class DataCreate(BaseModel):
    Image: Optional[str] = None
    H1: list[str] = Field(default_factory=list)
    H2: list[str] = Field(default_factory=list)
    H3: list[str] = Field(default_factory=list)
    H6: list[str] = Field(default_factory=list)


class DataUpdate(BaseModel):
    Image: Optional[str] = None
    H1: Optional[list[str]] = None
    H2: Optional[list[str]] = None
    H3: Optional[list[str]] = None
    H6: Optional[list[str]] = None


async def supabase_request(method, params=None, body=None):
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.request(
                method,
                TABLE_URL,
                headers={
                    **HEADERS,
                    "Prefer": "return=representation",
                },
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


# READ all records
@app.get("/data")
async def get_all_data():
    rows = await supabase_request(
        "GET",
        params={"select": "*", "order": "ID.asc"},
    )

    return [add_image_url(row) for row in rows]


# READ one record using UUID
@app.get("/data/{record_id}")
async def get_data(record_id: UUID):
    rows = await supabase_request(
        "GET",
        params={"select": "*", "ID": f"eq.{record_id}"},
    )

    if not rows:
        raise HTTPException(status_code=404, detail="Record not found")

    return add_image_url(rows[0])


# CREATE a record
@app.post("/data", status_code=201)
async def create_data(record: DataCreate):
    rows = await supabase_request(
        "POST",
        body=record.model_dump(),
    )
    return rows[0] if rows else {}


# UPDATE a record using UUID
@app.put("/data/{record_id}")
async def update_data(record_id: UUID, record: DataUpdate):
    updates = record.model_dump(exclude_unset=True)

    if not updates:
        raise HTTPException(status_code=400, detail="No fields provided")

    rows = await supabase_request(
        "PATCH",
        params={"ID": f"eq.{record_id}"},
        body=updates,
    )

    if not rows:
        raise HTTPException(status_code=404, detail="Record not found")

    return rows[0]


# DELETE a record using UUID
@app.delete("/data/{record_id}", status_code=204)
async def delete_data(record_id: UUID):
    rows = await supabase_request(
        "DELETE",
        params={"ID": f"eq.{record_id}"},
    )

    if not rows:
        raise HTTPException(status_code=404, detail="Record not found")

    return Response(status_code=204)
