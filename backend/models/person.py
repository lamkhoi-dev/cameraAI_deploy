"""Person detection result model — populated by AI Engine via API."""

from datetime import datetime
from sqlalchemy import DateTime, Float, Integer, String, Text, Index, func
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class Person(Base):
    __tablename__ = "persons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    person_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    camera_id: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)
    image_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    full_frame_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    bbox: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Clothing colors (JSON array)
    shirt_colors: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    pants_colors: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    hair_colors: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Metadata
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    frame_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    video_source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    track_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("idx_person_camera", "camera_id"),
        Index("idx_person_ts", "timestamp"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "person_id": self.person_id,
            "camera_id": self.camera_id,
            "location": self.location,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "image_path": self.image_path,
            "full_frame_path": self.full_frame_path,
            "bbox": self.bbox,
            "shirt_colors": self.shirt_colors or [],
            "pants_colors": self.pants_colors or [],
            "hair_colors": self.hair_colors or [],
            "confidence": self.confidence,
            "frame_index": self.frame_index,
            "video_source": self.video_source,
            "track_id": self.track_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
