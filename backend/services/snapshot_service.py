"""Background snapshot service: periodically captures thumbnails for cameras and caches them.

This service uses `camera_service.test_camera_connection` in a threadpool to capture a thumbnail
and stores base64-encoded JPEGs in memory for fast retrieval by `GET /api/cameras/{id}/display_image`.
"""
import asyncio
import base64
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from collections import OrderedDict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.camera import Camera
from services import camera_service
from database import async_session

logger = logging.getLogger(__name__)


class SnapshotService:
    """Snapshot service with TTL and max cache size (LRU eviction).

    - `poll_interval` controls how often the service scans cameras.
    - `max_cache_entries` limits in-memory entries.
    - Each cached entry has a timestamp and is considered fresh for its camera-specific `fallback_seconds`.
    """

    def __init__(self, poll_interval: int = 5, max_cache_entries: int = 200):
        self.poll_interval = poll_interval
        self.max_cache_entries = max_cache_entries
        self._task: Optional[asyncio.Task] = None
        self._stopped = asyncio.Event()
        # OrderedDict for LRU: camera_id -> {b64, timestamp}
        self._cache: "OrderedDict[str, Dict]" = OrderedDict()

    async def start(self):
        if self._task and not self._task.done():
            return
        self._stopped.clear()
        self._task = asyncio.create_task(self._run_loop())
        logger.info("SnapshotService started")

    async def stop(self):
        if self._task:
            self._stopped.set()
            await self._task
            logger.info("SnapshotService stopped")

    async def _run_loop(self):
        while not self._stopped.is_set():
            try:
                await self._capture_cycle()
            except Exception as e:
                logger.warning(f"SnapshotService cycle failed: {e}")
            try:
                await asyncio.wait_for(self._stopped.wait(), timeout=self.poll_interval)
            except asyncio.TimeoutError:
                continue

    async def _capture_cycle(self):
        # Fetch cameras and their fallback_seconds
        async with async_session() as db:  # type: AsyncSession
            result = await db.execute(select(Camera))
            cameras = result.scalars().all()

        now = datetime.utcnow()
        for cam in cameras:
            cam_id = cam.camera_id
            fallback_seconds = int(getattr(cam, "fallback_seconds", 5) or 5)
            freshness_window = timedelta(seconds=fallback_seconds)

            # If cache has fresh entry for this camera, skip
            cached = self._cache.get(cam_id)
            if cached:
                last_ts = cached.get("timestamp")
                if last_ts and (now - last_ts) < freshness_window:
                    # Move to end (most recently used)
                    self._cache.move_to_end(cam_id)
                    continue

            # Capture thumbnail in threadpool
            loop = asyncio.get_event_loop()
            try:
                res = await loop.run_in_executor(None, camera_service.test_camera_connection, cam.stream_url)
                if res and res.success and res.thumbnail_base64:
                    # Insert/update cache (LRU)
                    self._cache[cam_id] = {"b64": res.thumbnail_base64, "timestamp": datetime.utcnow()}
                    self._cache.move_to_end(cam_id)
                    # Evict oldest if exceeding size
                    while len(self._cache) > self.max_cache_entries:
                        evicted = self._cache.popitem(last=False)
                        logger.debug(f"Evicted snapshot cache entry: {evicted[0]}")
                    logger.debug(f"Snapshot captured for {cam_id}")
            except Exception as e:
                logger.debug(f"Snapshot capture failed for {cam_id}: {e}")

    def get_cached(self, camera_id: str) -> Optional[Dict]:
        entry = self._cache.get(camera_id)
        if entry:
            # refresh LRU position
            self._cache.move_to_end(camera_id)
        return entry


snapshot_service = SnapshotService()
