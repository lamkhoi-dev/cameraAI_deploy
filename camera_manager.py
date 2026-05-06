"""
Camera Manager - Stub implementation.
Manages RTSP camera stream connections.
When AI engine is active, it handles actual frame processing.
"""
import logging

logger = logging.getLogger(__name__)


class CameraManager:
    """Manages live camera stream connections and frame retrieval."""

    def __init__(self):
        self._cameras: dict = {}  # camera_id -> status dict
        self._running: dict = {}  # camera_id -> bool

    def add_camera(self, camera_id: str, rtsp_url: str, **kwargs) -> bool:
        """Register a camera stream."""
        self._cameras[camera_id] = {
            "camera_id": camera_id,
            "rtsp_url": rtsp_url,
            "running": False,
        }
        logger.info(f"Camera registered: {camera_id} -> {rtsp_url}")
        return True

    def remove_camera(self, camera_id: str) -> bool:
        """Unregister a camera stream."""
        self._cameras.pop(camera_id, None)
        self._running.pop(camera_id, None)
        logger.info(f"Camera removed: {camera_id}")
        return True

    def start_camera(self, camera_id: str) -> bool:
        """Start streaming for a camera."""
        if camera_id in self._cameras:
            self._cameras[camera_id]["running"] = True
            self._running[camera_id] = True
            logger.info(f"Camera started: {camera_id}")
            return True
        logger.warning(f"Camera not found: {camera_id}")
        return False

    def stop_camera(self, camera_id: str) -> bool:
        """Stop streaming for a camera."""
        if camera_id in self._cameras:
            self._cameras[camera_id]["running"] = False
            self._running[camera_id] = False
            logger.info(f"Camera stopped: {camera_id}")
            return True
        return False

    def get_frame_jpeg(self, camera_id: str) -> bytes | None:
        """
        Get latest JPEG frame for a camera.
        Returns None when AI engine is not running (no GPU).
        """
        return None

    def get_camera_status(self, camera_id: str) -> dict:
        """Get status for a specific camera."""
        if camera_id not in self._cameras:
            return {"camera_id": camera_id, "running": False, "error": "Not registered"}
        return self._cameras[camera_id]

    def get_all_status(self) -> dict:
        """Get status for all registered cameras."""
        return {cid: info.copy() for cid, info in self._cameras.items()}


# Singleton instance imported by app.py
camera_manager = CameraManager()
