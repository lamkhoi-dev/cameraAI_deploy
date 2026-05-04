"""Camera business logic — CRUD, test connection, stream management."""

import cv2
import base64
import time
import logging
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.camera import Camera
from schemas.camera import CameraCreate, CameraUpdate, CameraTestResult
from services.go2rtc_service import go2rtc_service

logger = logging.getLogger(__name__)


async def create_camera(db: AsyncSession, data: CameraCreate) -> Camera:
    camera = Camera(
        camera_id=data.camera_id,
        name=data.name,
        location=data.location,
        stream_url=data.stream_url,
        protocol=data.protocol,
        brand=data.brand,
        resolution=data.resolution,
        fps=data.fps,
        go2rtc_stream_name=data.camera_id,
        ai_detect_person=data.ai_detect_person,
        ai_detect_vehicle=data.ai_detect_vehicle,
        ai_detect_fire=data.ai_detect_fire,
        notes=data.notes,
    )
    db.add(camera)
    await db.commit()
    await db.refresh(camera)

    # Hot-add to go2rtc
    await go2rtc_service.add_stream(camera.camera_id, camera.stream_url)
    logger.info(f"Camera created: {camera.camera_id} ({camera.name})")
    return camera


async def get_camera(db: AsyncSession, camera_id: str) -> Camera | None:
    result = await db.execute(select(Camera).where(Camera.camera_id == camera_id))
    return result.scalar_one_or_none()


async def list_cameras(
    db: AsyncSession,
    page: int = 1,
    per_page: int = 50,
    location: str | None = None,
    is_active: bool | None = None,
) -> tuple[list[Camera], int]:
    query = select(Camera)
    count_query = select(func.count(Camera.id))

    if location:
        query = query.where(Camera.location.ilike(f"%{location}%"))
        count_query = count_query.where(Camera.location.ilike(f"%{location}%"))
    if is_active is not None:
        query = query.where(Camera.is_active == is_active)
        count_query = count_query.where(Camera.is_active == is_active)

    total = (await db.execute(count_query)).scalar() or 0
    query = query.order_by(Camera.camera_id).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    return list(result.scalars().all()), total


async def update_camera(db: AsyncSession, camera_id: str, data: CameraUpdate) -> Camera | None:
    camera = await get_camera(db, camera_id)
    if not camera:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(camera, key, value)

    await db.commit()
    await db.refresh(camera)

    # If stream URL changed, update go2rtc
    if "stream_url" in update_data:
        await go2rtc_service.remove_stream(camera.camera_id)
        await go2rtc_service.add_stream(camera.camera_id, camera.stream_url)

    return camera


async def delete_camera(db: AsyncSession, camera_id: str) -> bool:
    camera = await get_camera(db, camera_id)
    if not camera:
        return False

    await go2rtc_service.remove_stream(camera.camera_id)
    await db.delete(camera)
    await db.commit()
    logger.info(f"Camera deleted: {camera_id}")
    return True


def test_camera_connection(stream_url: str) -> CameraTestResult:
    """Test RTSP connection by grabbing 1 frame. Runs synchronously (in thread pool)."""
    start = time.time()
    try:
        cap = cv2.VideoCapture(stream_url)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        if not cap.isOpened():
            return CameraTestResult(success=False, error="Cannot open stream")

        ret, frame = cap.read()
        latency = int((time.time() - start) * 1000)
        cap.release()

        if not ret or frame is None:
            return CameraTestResult(success=False, latency_ms=latency, error="Cannot read frame")

        h, w = frame.shape[:2]
        resolution = f"{w}x{h}"

        # Encode thumbnail as base64 JPEG
        _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
        thumbnail = base64.b64encode(buf).decode("utf-8")

        return CameraTestResult(
            success=True,
            latency_ms=latency,
            resolution=resolution,
            thumbnail_base64=thumbnail,
        )

    except Exception as e:
        latency = int((time.time() - start) * 1000)
        return CameraTestResult(success=False, latency_ms=latency, error=str(e))
