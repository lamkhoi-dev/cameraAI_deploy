from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import Index
import json
import uuid

db = SQLAlchemy()

# ===== BẢNG NGƯỜI =====
class Person(db.Model):
    __tablename__ = 'persons'
    
    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    location = db.Column(db.String(255), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    image_path = db.Column(db.String(500), nullable=True)
    
    # Thông tin quần áo
    shirt_colors = db.Column(db.JSON, nullable=True)  # JSON array of colors
    pants_colors = db.Column(db.JSON, nullable=True)  # JSON array of colors
    hair_colors = db.Column(db.JSON, nullable=True)   # JSON array of colors
    
    # Metadata
    confidence = db.Column(db.Float, default=0.0)
    frame_index = db.Column(db.Integer, nullable=True)
    video_source = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes cho tìm kiếm
    __table_args__ = (
        Index('idx_person_timestamp', 'timestamp'),
        Index('idx_person_location', 'location'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'person_id': self.person_id,
            'location': self.location,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'image_path': self.image_path,
            'shirt_colors': self.shirt_colors or [],
            'pants_colors': self.pants_colors or [],
            'hair_colors': self.hair_colors or [],
            'confidence': self.confidence,
            'frame_index': self.frame_index,
            'video_source': self.video_source,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


# ===== BẢNG PHƯƠNG TIỆN =====
class Vehicle(db.Model):
    __tablename__ = 'vehicles'
    
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    vehicle_type = db.Column(db.String(50), nullable=False, index=True)  # car, motorcycle, bus, truck, bicycle
    license_plate = db.Column(db.String(50), nullable=True, index=True)
    
    # Màu sắc
    vehicle_colors = db.Column(db.JSON, nullable=True)  # JSON array of colors
    
    location = db.Column(db.String(255), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    image_path = db.Column(db.String(500), nullable=True)
    
    # Metadata
    confidence = db.Column(db.Float, default=0.0)
    frame_index = db.Column(db.Integer, nullable=True)
    video_source = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes cho tìm kiếm
    __table_args__ = (
        Index('idx_vehicle_timestamp', 'timestamp'),
        Index('idx_vehicle_location', 'location'),
        Index('idx_vehicle_type', 'vehicle_type'),
        Index('idx_license_plate', 'license_plate'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'vehicle_id': self.vehicle_id,
            'vehicle_type': self.vehicle_type,
            'license_plate': self.license_plate,
            'vehicle_colors': self.vehicle_colors or [],
            'location': self.location,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'image_path': self.image_path,
            'confidence': self.confidence,
            'frame_index': self.frame_index,
            'video_source': self.video_source,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


# ===== BẢNG CẢNH BÁO =====
class Alert(db.Model):
    __tablename__ = 'alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    alert_type = db.Column(db.String(50), nullable=False, index=True)  # fire, suspicious, missing_person, etc.
    person_id = db.Column(db.String(50), db.ForeignKey('persons.person_id'), nullable=True, index=True)
    vehicle_id = db.Column(db.String(50), db.ForeignKey('vehicles.vehicle_id'), nullable=True, index=True)
    
    description = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(255), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    frame_index = db.Column(db.Integer, nullable=True)
    
    image_path = db.Column(db.String(500), nullable=True)
    severity = db.Column(db.String(20), default='normal')  # low, normal, high, critical
    status = db.Column(db.String(20), default='active', index=True)  # active, resolved, false_alarm
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_alert_timestamp', 'timestamp'),
        Index('idx_alert_type', 'alert_type'),
        Index('idx_alert_status', 'status'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'alert_type': self.alert_type,
            'person_id': self.person_id,
            'vehicle_id': self.vehicle_id,
            'description': self.description,
            'location': self.location,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'frame_index': self.frame_index,
            'image_path': self.image_path,
            'severity': self.severity,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


# ===== BẢNG CAMERA =====
class Camera(db.Model):
    __tablename__ = 'cameras'
    
    id = db.Column(db.Integer, primary_key=True)
    camera_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(255), nullable=False, index=True)
    
    # RTSP/HTTPS stream URL
    stream_url = db.Column(db.String(500), nullable=False)
    protocol = db.Column(db.String(20), default='rtsp')  # rtsp, https, http, ws
    
    # Camera info
    resolution = db.Column(db.String(50), nullable=True)  # 1920x1080
    fps = db.Column(db.Integer, default=30)
    brand = db.Column(db.String(100), nullable=True)
    model = db.Column(db.String(100), nullable=True)
    
    # Authentication (nếu cần)
    username = db.Column(db.String(100), nullable=True)
    password = db.Column(db.String(100), nullable=True)
    
    # Status & monitoring
    is_active = db.Column(db.Boolean, default=True, index=True)
    is_recording = db.Column(db.Boolean, default=False)
    last_frame_timestamp = db.Column(db.DateTime, nullable=True)
    last_connection_status = db.Column(db.String(20), default='unknown')  # connected, disconnected, error
    
    # Settings
    enable_detection = db.Column(db.Boolean, default=True)
    enable_recording = db.Column(db.Boolean, default=False)
    recording_path = db.Column(db.String(500), nullable=True)
    
    notes = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_camera_location', 'location'),
        Index('idx_camera_is_active', 'is_active'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'camera_id': self.camera_id,
            'name': self.name,
            'location': self.location,
            'stream_url': self.stream_url,
            'protocol': self.protocol,
            'resolution': self.resolution,
            'fps': self.fps,
            'brand': self.brand,
            'model': self.model,
            'is_active': self.is_active,
            'is_recording': self.is_recording,
            'last_frame_timestamp': self.last_frame_timestamp.isoformat() if self.last_frame_timestamp else None,
            'last_connection_status': self.last_connection_status,
            'enable_detection': self.enable_detection,
            'enable_recording': self.enable_recording,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

