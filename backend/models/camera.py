"""Camera ORM model with per-camera AI layer toggles and AI configuration."""

import json
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Integer, String, Text, Index, func
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class Camera(Base):
    __tablename__ = "cameras"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    camera_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False)

    # Stream
    stream_url: Mapped[str] = mapped_column(String(500), nullable=False)
    protocol: Mapped[str] = mapped_column(String(20), default="rtsp")
    brand: Mapped[str | None] = mapped_column(String(100), nullable=True)
    resolution: Mapped[str | None] = mapped_column(String(50), nullable=True)
    fps: Mapped[int] = mapped_column(Integer, default=25)

    # Auth (stored separately from URL for flexibility)
    username: Mapped[str | None] = mapped_column(String(100), nullable=True)
    password_enc: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    connection_status: Mapped[str] = mapped_column(String(20), default="unknown")
    last_frame_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    go2rtc_stream_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # AI Layer Toggles — per-camera granularity
    ai_detect_person: Mapped[bool] = mapped_column(Boolean, default=True)
    ai_detect_vehicle: Mapped[bool] = mapped_column(Boolean, default=True)
    ai_detect_fire: Mapped[bool] = mapped_column(Boolean, default=False)

    # AI processing configuration
    ai_processing_fps: Mapped[int] = mapped_column(Integer, default=3)
    monitoring_interval_minutes: Mapped[int] = mapped_column(Integer, default=5)
    ai_region_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    patrol_region_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Display configuration for dashboard (seconds)
    display_interval_seconds: Mapped[int] = mapped_column(Integer, default=5)
    fallback_seconds: Mapped[int] = mapped_column(Integer, default=5)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_cam_location", "location"),
        Index("idx_cam_active", "is_active"),
    )

    def to_dict(self) -> dict:
        try:
            ai_region_points = json.loads(self.ai_region_json) if self.ai_region_json else None
        except Exception:
            ai_region_points = None

        return {
            "id": self.id,
            "camera_id": self.camera_id,
            "name": self.name,
            "location": self.location,
            "stream_url": self.stream_url,
            "protocol": self.protocol,
            "brand": self.brand,
            "resolution": self.resolution,
            "fps": self.fps,
            "is_active": self.is_active,
            "connection_status": self.connection_status,
            "last_frame_at": self.last_frame_at.isoformat() if self.last_frame_at else None,
            "go2rtc_stream_name": self.go2rtc_stream_name,
            "ai_detect_person": self.ai_detect_person,
            "ai_detect_vehicle": self.ai_detect_vehicle,
            "ai_detect_fire": self.ai_detect_fire,
            "ai_processing_fps": self.ai_processing_fps,
            "monitoring_interval_minutes": self.monitoring_interval_minutes,
            "ai_region_points": ai_region_points,
            "patrol_region_points": json.loads(self.patrol_region_json) if self.patrol_region_json else None,
            "display_interval_seconds": self.display_interval_seconds,
            "fallback_seconds": self.fallback_seconds,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
