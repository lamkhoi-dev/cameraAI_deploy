"""AI ingest router — receives detection results from AI Engine."""

import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.person import Person
from models.vehicle import Vehicle
from models.alert import Alert
from schemas.ai_ingest import (
    PersonResultPayload, VehicleResultPayload,
    AlertPayload, HeartbeatPayload, AIConfigResponse,
)
from services.ws_manager import ws_manager
from services import camera_service


def _naive_utc(dt: datetime | None) -> datetime:
    """Convert timezone-aware datetime to naive UTC for PostgreSQL."""
    if dt is None:
        return datetime.now(timezone.utc).replace(tzinfo=None)
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt

router = APIRouter(prefix="/api/ai", tags=["AI Ingest"])

# Store AI engine status in memory
ai_engine_status = {"status": "offline", "last_heartbeat": None, "cameras": []}


@router.post("/persons")
async def ingest_persons(data: PersonResultPayload, db: AsyncSession = Depends(get_db)):
    """Receive person detection results from AI Engine, save to DB, broadcast via WebSocket."""
    saved = []
    for p in data.persons:
        person = Person(
            person_id=f"p_{data.camera_id}_{uuid.uuid4().hex[:8]}",
            camera_id=data.camera_id,
            location=data.camera_id,
            timestamp=_naive_utc(data.timestamp),
            confidence=p.confidence,
            frame_index=data.frame_index,
            video_source=data.camera_id,
            track_id=p.track_id,
            image_path=p.image_path,
            full_frame_path=p.attributes.get("full_frame_path") if p.attributes else None,
            bbox=p.bbox or None,
            shirt_colors=p.attributes.get("shirt_colors") if p.attributes else None,
            pants_colors=p.attributes.get("pants_colors") if p.attributes else None,
            hair_colors=p.attributes.get("hair_colors") if p.attributes else None,
        )
        db.add(person)
        saved.append(person)

    await db.commit()

    # Broadcast to dashboards
    await ws_manager.broadcast("new_person_detected", {
        "camera_id": data.camera_id,
        "count": len(saved),
        "frame_index": data.frame_index,
    })

    return {"status": "ok", "saved": len(saved)}


@router.post("/vehicles")
async def ingest_vehicles(data: VehicleResultPayload, db: AsyncSession = Depends(get_db)):
    """Receive vehicle detection results from AI Engine."""
    saved = []
    for v in data.vehicles:
        vehicle = Vehicle(
            vehicle_id=f"v_{data.camera_id}_{uuid.uuid4().hex[:8]}",
            camera_id=data.camera_id,
            vehicle_type=v.vehicle_type,
            license_plate=v.license_plate,
            location=data.camera_id,
            timestamp=_naive_utc(data.timestamp),
            confidence=v.confidence,
            frame_index=data.frame_index,
            video_source=data.camera_id,
            track_id=v.track_id,
            image_path=v.image_path,
            full_frame_path=v.attributes.get("full_frame_path") if v.attributes else None,
            bbox=v.bbox or None,
            vehicle_colors=[c.model_dump() for c in v.colors] if v.colors else None,
        )
        db.add(vehicle)
        saved.append(vehicle)

    await db.commit()

    await ws_manager.broadcast("new_vehicle_detected", {
        "camera_id": data.camera_id,
        "count": len(saved),
    })

    return {"status": "ok", "saved": len(saved)}


@router.post("/alerts")
async def ingest_alert(data: AlertPayload, db: AsyncSession = Depends(get_db)):
    """Receive alert (fire/smoke/suspicious) from AI Engine."""
    alert = Alert(
        camera_id=data.camera_id,
        alert_type=data.alert_type,
        severity=data.severity,
        description=data.description,
        confidence=data.confidence,
        frame_index=data.frame_index,
        bbox=str(data.bbox) if data.bbox else None,
        snapshot_base64=data.snapshot_base64,
        timestamp=_naive_utc(data.timestamp),
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)

    await ws_manager.broadcast("new_alert", alert.to_dict())

    return {"status": "ok", "alert_id": alert.id}


@router.post("/heartbeat")
async def heartbeat(data: HeartbeatPayload):
    """AI Engine periodic ping — track health status."""
    ai_engine_status["status"] = data.status
    ai_engine_status["last_heartbeat"] = datetime.now(timezone.utc).isoformat()
    ai_engine_status["cameras"] = data.cameras_processing

    await ws_manager.broadcast("ai_engine_status", ai_engine_status)
    return {"status": "ok"}


@router.get("/config/{camera_id}", response_model=AIConfigResponse)
async def get_ai_config(camera_id: str, db: AsyncSession = Depends(get_db)):
    """AI Engine fetches per-camera config (which layers to run)."""
    camera = await camera_service.get_camera(db, camera_id)
    if not camera:
        return AIConfigResponse(
            camera_id=camera_id,
            stream_url="",
            ai_layers={"detect_person": False, "detect_vehicle": False, "detect_fire": False},
        )

    return AIConfigResponse(
        camera_id=camera.camera_id,
        stream_url=f"rtsp://localhost:8554/{camera.go2rtc_stream_name or camera.camera_id}",
        ai_layers={
            "detect_person": camera.ai_detect_person,
            "detect_vehicle": camera.ai_detect_vehicle,
            "detect_fire": camera.ai_detect_fire,
        },
        fps_target=3,
    )


@router.get("/status")
async def get_ai_status():
    """Get current AI Engine status."""
    return ai_engine_status
