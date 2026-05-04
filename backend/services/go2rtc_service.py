"""go2rtc service — manage streaming config and API calls."""

import httpx
import yaml
import logging
from pathlib import Path

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class Go2RTCService:
    """Manages go2rtc YAML config and hot-reload API."""

    def __init__(self):
        self.api_url = settings.go2rtc_api
        self.config_path = Path(settings.go2rtc_config_path)

    def build_rtsp_url(self, camera: dict) -> str:
        """Build RTSP URL from camera data, auto-detecting brand format."""
        url = camera.get("stream_url", "")
        if url:
            return url
        # Fallback: build from components
        ip = camera.get("ip", "")
        user = camera.get("username", "admin")
        pwd = camera.get("password", "")
        brand = (camera.get("brand") or "").lower()

        if "hikvision" in brand:
            return f"rtsp://{user}:{pwd}@192.168.1.{ip}:554/Streaming/Channels/101"
        elif "dahua" in brand or "pana" in brand:
            return f"rtsp://{user}:{pwd}@192.168.1.{ip}:554/cam/realmonitor?channel=1&subtype=0"
        return f"rtsp://{user}:{pwd}@192.168.1.{ip}:554/stream1"

    def generate_config(self, cameras: list[dict]) -> str:
        """Generate go2rtc.yaml from camera list."""
        config = {
            "api": {"listen": ":1984"},
            "rtsp": {"listen": ":8554"},
            "streams": {},
        }

        for cam in cameras:
            stream_name = cam.get("go2rtc_stream_name") or cam.get("camera_id")
            rtsp_url = self.build_rtsp_url(cam)
            if rtsp_url:
                config["streams"][stream_name] = [rtsp_url]

        return yaml.dump(config, default_flow_style=False, allow_unicode=True)

    def write_config(self, cameras: list[dict]):
        """Write go2rtc.yaml to disk."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        content = self.generate_config(cameras)
        self.config_path.write_text(content, encoding="utf-8")
        logger.info(f"go2rtc config written: {len(cameras)} streams")

    async def add_stream(self, stream_name: str, rtsp_url: str) -> bool:
        """Hot-add a stream via go2rtc API (no restart needed)."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.put(
                    f"{self.api_url}/api/streams",
                    params={"name": stream_name, "src": rtsp_url},
                )
                return resp.status_code < 400
        except httpx.HTTPError as e:
            logger.warning(f"Failed to add stream {stream_name}: {e}")
            return False

    async def remove_stream(self, stream_name: str) -> bool:
        """Remove a stream via go2rtc API."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.delete(
                    f"{self.api_url}/api/streams",
                    params={"name": stream_name},
                )
                return resp.status_code < 400
        except httpx.HTTPError as e:
            logger.warning(f"Failed to remove stream {stream_name}: {e}")
            return False

    async def get_streams(self) -> dict:
        """Get all active streams from go2rtc."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{self.api_url}/api/streams")
                if resp.status_code == 200:
                    return resp.json()
        except httpx.HTTPError as e:
            logger.warning(f"Failed to get streams: {e}")
        return {}

    async def check_health(self) -> bool:
        """Check if go2rtc is running."""
        try:
            async with httpx.AsyncClient(timeout=3) as client:
                resp = await client.get(f"{self.api_url}/api")
                return resp.status_code == 200
        except httpx.HTTPError:
            return False


go2rtc_service = Go2RTCService()
