"""Camera CRUD router — management + AI layer toggles + test connection."""

import asyncio
from fastapi import APIRouter, Depends, HTTPException, Query
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

router = APIRouter(prefix="/api/cameras", tags=["Cameras"])


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
