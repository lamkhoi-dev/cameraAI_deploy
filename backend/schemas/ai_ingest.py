"""AI ingest request schemas — contract between AI Engine and Backend."""

from pydantic import BaseModel, Field
from datetime import datetime


class ColorInfo(BaseModel):
    rank: int = 1
    name: str = ""
    rgb: list[int] = Field(default_factory=lambda: [0, 0, 0])


class PersonDetection(BaseModel):
    track_id: int | None = None
    confidence: float = 0.0
    bbox: list[int] = Field(default_factory=list)
    attributes: dict | None = None
    image_path: str | None = None
    crop_image_base64: str | None = None


class PersonResultPayload(BaseModel):
    """POST /api/ai/persons — sent by AI Engine."""
    camera_id: str
    frame_index: int | None = None
    timestamp: datetime | None = None
    persons: list[PersonDetection] = Field(default_factory=list)


class VehicleDetection(BaseModel):
    track_id: int | None = None
    vehicle_type: str = "unknown"
    license_plate: str | None = None
    confidence: float = 0.0
    bbox: list[int] = Field(default_factory=list)
    colors: list[ColorInfo] = Field(default_factory=list)
    image_path: str | None = None
    crop_image_base64: str | None = None


class VehicleResultPayload(BaseModel):
    """POST /api/ai/vehicles — sent by AI Engine."""
    camera_id: str
    frame_index: int | None = None
    timestamp: datetime | None = None
    vehicles: list[VehicleDetection] = Field(default_factory=list)


class AlertPayload(BaseModel):
    """POST /api/ai/alerts — sent by AI Engine."""
    camera_id: str
    alert_type: str = Field(..., examples=["fire", "smoke", "suspicious"])
    severity: str = Field(default="normal", examples=["low", "normal", "high", "critical"])
    description: str | None = None
    confidence: float = 0.0
    frame_index: int | None = None
    bbox: list[int] | None = None
    snapshot_base64: str | None = None
    timestamp: datetime | None = None


class HeartbeatPayload(BaseModel):
    """POST /api/ai/heartbeat — AI Engine ping."""
    status: str = "alive"
    cameras_processing: list[str] = Field(default_factory=list)
    fps_total: float | None = None
    gpu_usage_percent: float | None = None
    vram_usage_mb: float | None = None


class AIConfigResponse(BaseModel):
    """GET /api/ai/config/{cam_id} — AI Engine fetches config."""
    camera_id: str
    stream_url: str
    ai_layers: dict
    fps_target: int = 3
    resolution: str = "640x480"
