"""
API Client Module - Push AI results to Backend API
"""

import asyncio
import httpx
import logging
from typing import List, Dict, Optional
from datetime import datetime


logger = logging.getLogger(__name__)


class AIResultClient:
    """
    Push AI engine results to Backend API
    Supports async/non-blocking operations
    """
    
    def __init__(self, backend_url: str, api_key: str = "", timeout: int = 10):
        """
        Args:
            backend_url: Backend API URL (e.g., 'http://localhost:8000')
            api_key: API key for authentication
            timeout: Request timeout in seconds
        """
        self.backend_url = backend_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.headers = {}
        
        if api_key:
            self.headers["X-API-Key"] = api_key
        
        self.client = None
    
    async def connect(self):
        """Establish connection"""
        if self.client is None:
            self.client = httpx.AsyncClient(timeout=self.timeout, headers=self.headers)
    
    async def disconnect(self):
        """Close connection"""
        if self.client:
            await self.client.aclose()
            self.client = None
    
    async def push_persons(self, camera_id: str, frame_idx: int, persons: List[Dict]):
        """
        Push person detection results
        
        Args:
            camera_id: Camera ID
            frame_idx: Frame index
            persons: List of detected persons
        """
        await self.connect()
        
        payload = {
            "camera_id": camera_id,
            "frame_index": frame_idx,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "persons": persons
        }
        
        try:
            response = await self.client.post(
                f"{self.backend_url}/api/ai/persons",
                json=payload
            )
            response.raise_for_status()
            logger.debug(f"✓ Pushed {len(persons)} persons from {camera_id}")
        except Exception as e:
            logger.error(f"✗ Failed to push persons: {e}")
    
    async def push_vehicles(self, camera_id: str, frame_idx: int, vehicles: List[Dict]):
        """
        Push vehicle detection results
        
        Args:
            camera_id: Camera ID
            frame_idx: Frame index
            vehicles: List of detected vehicles
        """
        await self.connect()
        
        payload = {
            "camera_id": camera_id,
            "frame_index": frame_idx,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "vehicles": vehicles
        }
        
        try:
            response = await self.client.post(
                f"{self.backend_url}/api/ai/vehicles",
                json=payload
            )
            response.raise_for_status()
            logger.debug(f"✓ Pushed {len(vehicles)} vehicles from {camera_id}")
        except Exception as e:
            logger.error(f"✗ Failed to push vehicles: {e}")
    
    async def push_alert(self, camera_id: str, frame_idx: int, alert_type: str, 
                        severity: str = "medium", confidence: float = 0.0, 
                        bbox: Optional[List] = None, snapshot_path: Optional[str] = None):
        """
        Push alert (fire, smoke, suspicious activity, etc.)
        
        Args:
            camera_id: Camera ID
            frame_idx: Frame index
            alert_type: Type of alert ('fire', 'smoke', 'intrusion', etc.)
            severity: Severity level ('low', 'medium', 'high')
            confidence: Confidence score (0-1)
            bbox: Bounding box [x1, y1, x2, y2]
            snapshot_path: Path to alert snapshot
        """
        await self.connect()
        
        payload = {
            "camera_id": camera_id,
            "frame_index": frame_idx,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "alert_type": alert_type,
            "severity": severity,
            "confidence": confidence,
            "bbox": bbox,
            "snapshot_path": snapshot_path
        }
        
        try:
            response = await self.client.post(
                f"{self.backend_url}/api/ai/alerts",
                json=payload
            )
            response.raise_for_status()
            logger.info(f"✓ Pushed {alert_type} alert from {camera_id} (severity: {severity})")
        except Exception as e:
            logger.error(f"✗ Failed to push alert: {e}")
    
    async def push_faces(self, camera_id: str, frame_idx: int, person_id: str, faces: List[Dict], 
                        matched_person: Optional[Dict] = None):
        """
        Push face detection and recognition results (Phase 2)
        
        Args:
            camera_id: Camera ID
            frame_idx: Frame index
            person_id: Detected person ID
            faces: List of face detections with embeddings
            matched_person: Matched known person (if FaceID found a match)
        """
        await self.connect()
        
        # Remove embeddings from face data before sending (optional, to reduce payload)
        faces_to_send = []
        for face in faces:
            face_copy = face.copy()
            # Keep embedding for now - remove if too large
            faces_to_send.append(face_copy)
        
        payload = {
            "camera_id": camera_id,
            "frame_index": frame_idx,
            "person_id": person_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "faces": faces_to_send,
            "matched_person": matched_person
        }
        
        try:
            response = await self.client.post(
                f"{self.backend_url}/api/ai/faces",
                json=payload
            )
            response.raise_for_status()
            logger.debug(f"✓ Pushed {len(faces)} faces for person {person_id}")
        except Exception as e:
            logger.error(f"✗ Failed to push faces: {e}")
    
    async def push_heartbeat(self, status: str = "running", cameras_processing: List[str] = None,
                           fps_avg: float = 0.0, gpu_usage_percent: float = 0.0,
                           models_loaded: List[str] = None):
        """
        Push heartbeat (status check)
        
        Args:
            status: Engine status ('running', 'error', 'initializing')
            cameras_processing: List of camera IDs being processed
            fps_avg: Average FPS
            gpu_usage_percent: GPU usage percentage
            models_loaded: List of loaded models
        """
        await self.connect()
        
        payload = {
            "status": status,
            "cameras_processing": cameras_processing or [],
            "fps_avg": fps_avg,
            "gpu_usage_percent": gpu_usage_percent,
            "models_loaded": models_loaded or [],
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        try:
            response = await self.client.post(
                f"{self.backend_url}/api/ai/heartbeat",
                json=payload
            )
            response.raise_for_status()
        except Exception as e:
            logger.debug(f"⚠️  Heartbeat push failed: {e}")


def create_api_client(backend_url: str, api_key: str = "") -> AIResultClient:
    """Factory function to create API client"""
    return AIResultClient(backend_url, api_key)
