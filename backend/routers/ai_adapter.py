"""AI Adapter — backward compatibility with old db_integration.py format.

The old AI code (main.py) uses DetectionDataUploader which calls:
  POST /api/persons  (flat JSON)
  POST /api/vehicles (flat JSON)
  POST /api/alerts   (flat JSON)

This adapter accepts the OLD format and transforms it to the new schema.
"""

import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.person import Person
from models.vehicle import Vehicle
from models.alert import Alert
from services.ws_manager import ws_manager

router = APIRouter(prefix="/api", tags=["AI Adapter (Legacy)"])


@router.post("/persons")
async def legacy_create_person(data: dict, db: AsyncSession = Depends(get_db)):
    """Accept old format from db_integration.py DetectionDataUploader.upload_person()."""
    person = Person(
        person_id=data.get("person_id", f"p_{uuid.uuid4().hex[:8]}"),
        camera_id=data.get("video_source"),
        location=data.get("location"),
        timestamp=datetime.now(timezone.utc),
        image_path=data.get("image_path"),
        shirt_colors=data.get("shirt_colors"),
        pants_colors=data.get("pants_colors"),
        hair_colors=data.get("hair_colors"),
        confidence=data.get("confidence", 0.0),
        frame_index=data.get("frame_index"),
        video_source=data.get("video_source"),
        notes=data.get("notes"),
    )
    db.add(person)
    await db.commit()
    await db.refresh(person)

    await ws_manager.broadcast("new_person_detected", {
        "camera_id": data.get("video_source", "unknown"),
        "count": 1,
    })

    return {"status": "success", "id": person.id, "person_id": person.person_id}


@router.post("/vehicles")
async def legacy_create_vehicle(data: dict, db: AsyncSession = Depends(get_db)):
    """Accept old format from db_integration.py DetectionDataUploader.upload_vehicle()."""
    vehicle = Vehicle(
        vehicle_id=data.get("vehicle_id", f"v_{uuid.uuid4().hex[:8]}"),
        camera_id=data.get("video_source"),
        vehicle_type=data.get("vehicle_type", "unknown"),
        license_plate=data.get("license_plate"),
        vehicle_colors=data.get("vehicle_colors"),
        location=data.get("location"),
        timestamp=datetime.now(timezone.utc),
        image_path=data.get("image_path"),
        confidence=data.get("confidence", 0.0),
        frame_index=data.get("frame_index"),
        video_source=data.get("video_source"),
        notes=data.get("notes"),
    )
    db.add(vehicle)
    await db.commit()
    await db.refresh(vehicle)

    await ws_manager.broadcast("new_vehicle_detected", {
        "camera_id": data.get("video_source", "unknown"),
        "count": 1,
    })

    return {"status": "success", "id": vehicle.id, "vehicle_id": vehicle.vehicle_id}


@router.post("/alerts")
async def legacy_create_alert(data: dict, db: AsyncSession = Depends(get_db)):
    """Accept old format from db_integration.py DetectionDataUploader.upload_alert()."""
    alert = Alert(
        camera_id=data.get("location", "unknown"),
        alert_type=data.get("alert_type", "unknown"),
        severity=data.get("severity", "normal"),
        status=data.get("status", "active"),
        description=data.get("description"),
        frame_index=data.get("frame_index"),
        image_path=data.get("image_path"),
        location=data.get("location"),
        timestamp=datetime.now(timezone.utc),
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)

    await ws_manager.broadcast("new_alert", alert.to_dict())

    return {"status": "success", "id": alert.id}
