"""Camera CRUD router — management + AI layer toggles + test connection."""

import asyncio
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from routers.auth import get_current_user, require_admin
from models.user import User
from schemas.camera import (
    CameraCreate, CameraUpdate, CameraResponse,
    CameraListResponse, CameraTestResult, AILayerToggle,
)
from services import camera_service
from services.ws_manager import ws_manager
from sqlalchemy import select, func
from models.person import Person
from models.vehicle import Vehicle
from datetime import datetime, timedelta
import os
from pathlib import Path
import base64
import asyncio
from services.snapshot_service import snapshot_service

router = APIRouter(prefix="/api/cameras", tags=["Cameras"])
CROPS_DIR = Path(os.getenv("CROPS_DIR", "cropped_data")).resolve()


def _display_payload_from_path(raw_path: str | None, bbox: list | None, confidence: float, timestamp: datetime) -> dict | None:
    if not raw_path:
        return None

    normalized = str(raw_path).replace("\\", "/").strip()
    if not normalized:
        return None

    if normalized.startswith("/api/crops/"):
        return {
            "type": "ai",
            "image_url": normalized,
            "bbox": bbox,
            "confidence": float(confidence),
            "timestamp": timestamp.isoformat(),
        }

    if "/cropped_data/" in normalized:
        rel = normalized.split("/cropped_data/", 1)[1].lstrip("/")
        return {
            "type": "ai",
            "image_url": f"/api/crops/{rel}",
            "bbox": bbox,
            "confidence": float(confidence),
            "timestamp": timestamp.isoformat(),
        }

    path = Path(normalized)
    if not path.is_absolute():
        candidate = (CROPS_DIR / path).resolve()
        if candidate.exists():
            try:
                rel = candidate.relative_to(CROPS_DIR)
                return {
                    "type": "ai",
                    "image_url": f"/api/crops/{rel.as_posix()}",
                    "bbox": bbox,
                    "confidence": float(confidence),
                    "timestamp": timestamp.isoformat(),
                }
            except Exception:
                path = candidate

    if path.exists():
        try:
            rel = path.resolve().relative_to(CROPS_DIR)
            return {
                "type": "ai",
                "image_url": f"/api/crops/{rel.as_posix()}",
                "bbox": bbox,
                "confidence": float(confidence),
                "timestamp": timestamp.isoformat(),
            }
        except Exception:
            raw = path.read_bytes()
            b64 = base64.b64encode(raw).decode("utf-8")
            return {
                "type": "ai",
                "image_base64": b64,
                "bbox": bbox,
                "confidence": float(confidence),
                "timestamp": timestamp.isoformat(),
            }

    return None


@router.post("", response_model=CameraResponse, status_code=201)
async def create_camera(
    data: CameraCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
):
    existing = await camera_service.get_camera(db, data.camera_id)
    if existing:
        raise HTTPException(status_code=409, detail=f"Camera {data.camera_id} already exists")

    camera = await camera_service.create_camera(db, data)
    await ws_manager.broadcast("camera_added", camera.to_dict())
    return camera


@router.get("", response_model=CameraListResponse)
async def list_cameras(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    location: str | None = None,
    is_active: bool | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    cameras, total = await camera_service.list_cameras(db, page, per_page, location, is_active)
    return CameraListResponse(
        cameras=[CameraResponse.model_validate(c) for c in cameras],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/{camera_id}", response_model=CameraResponse)
async def get_camera(
    camera_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    camera = await camera_service.get_camera(db, camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    return camera


@router.put("/{camera_id}", response_model=CameraResponse)
async def update_camera(
    camera_id: str,
    data: CameraUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
):
    camera = await camera_service.update_camera(db, camera_id, data)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    await ws_manager.broadcast("camera_updated", camera.to_dict())
    return camera


@router.delete("/{camera_id}", status_code=204)
async def delete_camera(
    camera_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
):
    deleted = await camera_service.delete_camera(db, camera_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Camera not found")
    await ws_manager.broadcast("camera_deleted", {"camera_id": camera_id})


@router.post("/{camera_id}/test", response_model=CameraTestResult)
async def test_connection(
    camera_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    camera = await camera_service.get_camera(db, camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    # Run OpenCV test in thread pool (blocking I/O)
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None, camera_service.test_camera_connection, camera.stream_url
    )
    return result


@router.patch("/{camera_id}/ai-layers", response_model=CameraResponse)
async def toggle_ai_layers(
    camera_id: str,
    data: AILayerToggle,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
):
    """Toggle AI detection layers for a specific camera."""
    camera = await camera_service.get_camera(db, camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    if data.detect_person is not None:
        camera.ai_detect_person = data.detect_person
    if data.detect_vehicle is not None:
        camera.ai_detect_vehicle = data.detect_vehicle
    if data.detect_fire is not None:
        camera.ai_detect_fire = data.detect_fire

    await db.commit()
    await db.refresh(camera)

    await ws_manager.broadcast("camera_ai_config_changed", {
        "camera_id": camera_id,
        "ai_layers": {
            "detect_person": camera.ai_detect_person,
            "detect_vehicle": camera.ai_detect_vehicle,
            "detect_fire": camera.ai_detect_fire,
        },
    })
    return camera


@router.get("/{camera_id}/display_image")
async def get_display_image(
    camera_id: str,
    display_interval: int | None = None,
    fallback_seconds: int | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Return representative AI-processed image for dashboard or a fallback camera frame.

    Logic:
    - If any AI result (person or vehicle) exists within the last `display_interval` seconds,
      return the highest-confidence result's image URL.
    - Otherwise, if the last AI result is older than `fallback_seconds`, capture a frame
      from the camera and return it as base64 JPEG.
    - Otherwise return 204 waiting.
    """
    camera = await camera_service.get_camera(db, camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    # Determine intervals
    display_interval = int(display_interval or camera.display_interval_seconds or 5)
    fallback_seconds = int(fallback_seconds or camera.fallback_seconds or 5)

    now = datetime.utcnow()
    cutoff = now - timedelta(seconds=display_interval)

    # Query best person and vehicle within window
    person_q = select(Person).where(Person.camera_id == camera_id, Person.timestamp >= cutoff).order_by(Person.confidence.desc()).limit(1)
    vehicle_q = select(Vehicle).where(Vehicle.camera_id == camera_id, Vehicle.timestamp >= cutoff).order_by(Vehicle.confidence.desc()).limit(1)

    p_res = await db.execute(person_q)
    best_person = p_res.scalars().first()
    v_res = await db.execute(vehicle_q)
    best_vehicle = v_res.scalars().first()

    # Choose best by confidence
    best = None
    if best_person and best_vehicle:
        best = best_person if best_person.confidence >= best_vehicle.confidence else best_vehicle
    elif best_person:
        best = best_person
    elif best_vehicle:
        best = best_vehicle

    if best:
        bbox = getattr(best, "bbox", None)
        full_frame_path = getattr(best, "full_frame_path", None)
        image_path = getattr(best, "image_path", None)

        payload = _display_payload_from_path(full_frame_path, bbox, best.confidence, best.timestamp)
        if payload:
            return payload

        payload = _display_payload_from_path(image_path, bbox, best.confidence, best.timestamp)
        if payload:
            return payload

    # No AI image available within window — check last AI timestamp
    last_person_q = select(func.max(Person.timestamp)).where(Person.camera_id == camera_id)
    last_vehicle_q = select(func.max(Vehicle.timestamp)).where(Vehicle.camera_id == camera_id)
    last_p = (await db.execute(last_person_q)).scalar()
    last_v = (await db.execute(last_vehicle_q)).scalar()

    last_ai_ts = None
    if last_p and last_v:
        last_ai_ts = last_p if last_p >= last_v else last_v
    elif last_p:
        last_ai_ts = last_p
    elif last_v:
        last_ai_ts = last_v

    if (not last_ai_ts) or (now - last_ai_ts >= timedelta(seconds=fallback_seconds)):
        # Try cached snapshot first (fast)
        cached = snapshot_service.get_cached(camera_id)
        if cached and cached.get("b64"):
            return {"type": "fallback", "image_base64": cached["b64"], "timestamp": cached.get("timestamp").isoformat()}

        # As a last resort, attempt an on-demand capture (may be slow)
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, camera_service.test_camera_connection, camera.stream_url)
        if result and result.success and result.thumbnail_base64:
            return {"type": "fallback", "image_base64": result.thumbnail_base64, "timestamp": datetime.utcnow().isoformat()}

        raise HTTPException(status_code=503, detail="Unable to fetch fallback frame")

    # Otherwise, still within wait window
    return Response(status_code=204)
