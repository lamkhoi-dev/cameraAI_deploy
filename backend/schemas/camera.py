"""Camera request/response schemas."""

from pydantic import BaseModel, Field, model_validator
from datetime import datetime
import json


class CameraCreate(BaseModel):
    camera_id: str = Field(..., max_length=50, examples=["cam_01"])
    name: str = Field(..., max_length=255, examples=["Sảnh A"])
    location: str = Field(..., max_length=255, examples=["Tầng 1 - Sảnh chính"])
    stream_url: str = Field(..., max_length=500, examples=["rtsp://admin:pass@192.168.1.127:554/Streaming/Channels/101"])
    protocol: str = Field(default="rtsp", pattern="^(rtsp|http|https)$")
    brand: str | None = Field(default=None, examples=["Hikvision"])
    resolution: str | None = Field(default=None, examples=["1920x1080"])
    fps: int = Field(default=25, ge=1, le=60)
    ai_detect_person: bool = True
    ai_detect_vehicle: bool = True
    ai_detect_fire: bool = False
    ai_processing_fps: int = Field(default=3, ge=1, le=30)
    monitoring_interval_minutes: int = Field(default=5, ge=1, le=60)
    ai_region_points: list[list[float]] | None = None
    patrol_region_points: list[list[float]] | None = None
    display_interval_seconds: int = Field(default=5, ge=1, le=60)
    fallback_seconds: int = Field(default=5, ge=1, le=60)
    notes: str | None = None


class CameraUpdate(BaseModel):
    name: str | None = None
    location: str | None = None
    stream_url: str | None = None
    protocol: str | None = None
    brand: str | None = None
    resolution: str | None = None
    fps: int | None = Field(default=None, ge=1, le=60)
    is_active: bool | None = None
    ai_detect_person: bool | None = None
    ai_detect_vehicle: bool | None = None
    ai_detect_fire: bool | None = None
    ai_processing_fps: int | None = Field(default=None, ge=1, le=30)
    monitoring_interval_minutes: int | None = Field(default=None, ge=1, le=60)
    ai_region_points: list[list[float]] | None = None
    patrol_region_points: list[list[float]] | None = None
    display_interval_seconds: int | None = Field(default=None, ge=1, le=60)
    fallback_seconds: int | None = Field(default=None, ge=1, le=60)
    notes: str | None = None


class AILayerToggle(BaseModel):
    """Toggle AI detection layers for a camera."""
    detect_person: bool | None = None
    detect_vehicle: bool | None = None
    detect_fire: bool | None = None


class CameraResponse(BaseModel):
    id: int
    camera_id: str
    name: str
    location: str
    stream_url: str
    protocol: str
    brand: str | None
    resolution: str | None
    fps: int
    is_active: bool
    connection_status: str
    last_frame_at: datetime | None
    go2rtc_stream_name: str | None
    ai_detect_person: bool
    ai_detect_vehicle: bool
    ai_detect_fire: bool
    ai_processing_fps: int = 3
    monitoring_interval_minutes: int = 5
    ai_region_points: list[list[float]] | None = None
    patrol_region_points: list[list[float]] | None = None
    display_interval_seconds: int = 5
    fallback_seconds: int = 5
    notes: str | None
    created_at: datetime | None
    updated_at: datetime | None

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def parse_region_json(cls, data):
        """Convert ORM ai_region_json/patrol_region_json strings to lists."""
        if hasattr(data, "__dict__"):
            # ORM object — read attributes
            obj = data
            result = {}
            for field_name in cls.model_fields:
                result[field_name] = getattr(obj, field_name, None)
            # Parse JSON strings into lists
            raw_ai = getattr(obj, "ai_region_json", None)
            raw_patrol = getattr(obj, "patrol_region_json", None)
            try:
                result["ai_region_points"] = json.loads(raw_ai) if raw_ai else None
            except Exception:
                result["ai_region_points"] = None
            try:
                result["patrol_region_points"] = json.loads(raw_patrol) if raw_patrol else None
            except Exception:
                result["patrol_region_points"] = None
            return result
        return data


class CameraTestResult(BaseModel):
    success: bool
    latency_ms: int | None = None
    resolution: str | None = None
    thumbnail_base64: str | None = None
    error: str | None = None


class CameraListResponse(BaseModel):
    cameras: list[CameraResponse]
    total: int
    page: int
    per_page: int
