"""Alert model — fire, smoke, suspicious activity."""

from datetime import datetime
from sqlalchemy import DateTime, Float, Integer, String, Text, Index, func
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    camera_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(20), default="normal")
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)

    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    frame_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    image_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    snapshot_base64: Mapped[str | None] = mapped_column(Text, nullable=True)
    bbox: Mapped[str | None] = mapped_column(String(200), nullable=True)

    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)

    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    resolved_by: Mapped[str | None] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("idx_alert_camera", "camera_id"),
        Index("idx_alert_type_status", "alert_type", "status"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "camera_id": self.camera_id,
            "alert_type": self.alert_type,
            "severity": self.severity,
            "status": self.status,
            "description": self.description,
            "confidence": self.confidence,
            "frame_index": self.frame_index,
            "image_path": self.image_path,
            "bbox": self.bbox,
            "location": self.location,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolved_by": self.resolved_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
