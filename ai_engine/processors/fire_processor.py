"""
Fire Processor Module - Fire & Smoke Detection
Replaces HSV color thresholding with YOLO-based detection
"""

import cv2
import numpy as np
from ultralytics import YOLO
from typing import Dict, List, Optional
from collections import defaultdict
import logging

from ..config import (
    CONF_THRESHOLD, CROPPED_DATA_DIR, FIRE_TEMPORAL_THRESHOLD,
    FIRE_MINIMUM_AREA, USE_GPU, GPU_DEVICE
)
from .base_processor import BaseProcessor


logger = logging.getLogger(__name__)


class FireProcessor(BaseProcessor):
    """Fire and Smoke Detection using YOLO"""
    
    def __init__(self, model_path: str):
        """
        Args:
            model_path: Path to YOLO11n fire/smoke detection model
        """
        super().__init__(model_path)
        self.fire_tracks = defaultdict(int)  # Track consecutive fire detections
    
    def load_model(self):
        """Load fire/smoke detection model"""
        try:
            device = 0 if USE_GPU else 'cpu'
            self.model = YOLO(self.model_name)
            logger.info(f"✓ Fire model loaded: {self.model_name}")
            return True
        except Exception as e:
            logger.warning(f"⚠️  Fire model not loaded (optional): {e}")
            return False
    
    def process(self, frame: np.ndarray, frame_idx: int) -> Dict:
        """
        Detect fire and smoke
        
        Args:
            frame: Input BGR frame
            frame_idx: Frame index for temporal filtering
            
        Returns:
            Dict: {
                'alerts': [
                    {
                        'type': 'fire' or 'smoke',
                        'confidence': 0.87,
                        'bbox': [x1, y1, x2, y2],
                        'area': 1500,
                        'snapshot_path': '...'
                    }
                ],
                'confirmed': True/False  # If temporal threshold met
            }
        """
        alerts = {'alerts': [], 'confirmed': False}
        
        if self.model is None:
            return alerts
        
        try:
            # Run detection
            results = self.model.predict(
                frame,
                conf=CONF_THRESHOLD,
                verbose=False
            )
            
            frame_alerts = []
            if results and results[0].boxes:
                for box in results[0].boxes:
                    conf = float(box.conf)
                    class_id = int(box.cls)
                    
                    if conf >= CONF_THRESHOLD:
                        bbox = box.xyxy[0].cpu().numpy().astype(int).tolist()
                        x1, y1, x2, y2 = bbox
                        area = (x2 - x1) * (y2 - y1)
                        
                        # Filter by minimum area
                        if area >= FIRE_MINIMUM_AREA:
                            # Get class name (assuming 0=fire, 1=smoke)
                            class_name = self._get_class_name(class_id)
                            
                            frame_alerts.append({
                                'type': class_name,
                                'confidence': conf,
                                'bbox': bbox,
                                'area': area
                            })
            
            # Temporal filtering - confirm fire only if detected in multiple consecutive frames
            if frame_alerts:
                self.fire_tracks[frame_idx] = len(frame_alerts)
                
                # Check if fire confirmed in last N frames
                consecutive_count = self._count_consecutive_detections(frame_idx)
                if consecutive_count >= FIRE_TEMPORAL_THRESHOLD:
                    alerts['confirmed'] = True
                    
                    # Save snapshot and update alerts
                    for alert in frame_alerts:
                        snapshot_path = self._save_fire_snapshot(frame, alert['bbox'], frame_idx)
                        alert['snapshot_path'] = snapshot_path
                        frame_alerts.append(alert)
            
            alerts['alerts'] = frame_alerts
            return alerts
            
        except Exception as e:
            logger.error(f"✗ Fire processing error: {e}")
            return alerts
    
    def _get_class_name(self, class_id: int) -> str:
        """Get class name from ID"""
        class_names = {
            0: 'fire',
            1: 'smoke'
        }
        return class_names.get(class_id, 'unknown')
    
    def _count_consecutive_detections(self, current_frame: int) -> int:
        """Count consecutive frames with fire detection"""
        count = 0
        for i in range(current_frame, max(current_frame - FIRE_TEMPORAL_THRESHOLD - 1, -1), -1):
            if i in self.fire_tracks:
                count += 1
            else:
                break
        return count
    
    def _save_fire_snapshot(self, frame: np.ndarray, bbox: List[int], frame_idx: int) -> str:
        """Save fire/smoke detection snapshot"""
        try:
            alert_dir = CROPPED_DATA_DIR / "fire_alerts"
            alert_dir.mkdir(parents=True, exist_ok=True)
            
            # Crop alert region
            x1, y1, x2, y2 = bbox
            alert_crop = frame[max(0, y1):min(frame.shape[0], y2), max(0, x1):min(frame.shape[1], x2)]
            
            snapshot_path = alert_dir / f"frame_{frame_idx}_alert.jpg"
            cv2.imwrite(str(snapshot_path), alert_crop)
            
            return str(snapshot_path)
        except Exception as e:
            logger.warning(f"⚠️  Failed to save fire snapshot: {e}")
            return ""
    
    def postprocess(self, results) -> Dict:
        """Postprocess fire detection results"""
        return {'alerts': [], 'confirmed': False}
