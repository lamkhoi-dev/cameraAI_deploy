"""
Vehicle Processor Module - Vehicle Detection + Classification + License Plate Recognition
"""

import cv2
import numpy as np
from ultralytics import YOLO
from typing import List, Dict, Optional
import logging

from ..utils.color_analyzer import ColorAnalyzer
from ..utils.plate_reader import PlateReader
from ..utils.roi_utils import apply_roi_mask
from ..config import (
    CONF_THRESHOLD, TRACK_CONF_THRESHOLD, NUM_COLORS_VEHICLE,
    CROPPED_DATA_DIR, VEHICLE_CLASSES, USE_PLATE_DETECTION, USE_OCR,
    USE_GPU, GPU_DEVICE
)
from .base_processor import BaseProcessor


logger = logging.getLogger(__name__)


class VehicleProcessor(BaseProcessor):
    """Vehicle detection, classification, and license plate recognition"""
    
    def __init__(self, model_path: str):
        """
        Args:
            model_path: Path to YOLOv11s model
        """
        super().__init__(model_path)
        self.color_analyzer = ColorAnalyzer(num_colors=NUM_COLORS_VEHICLE)
        
        # Initialize plate reader if OCR is enabled
        self.plate_reader = None
        if USE_PLATE_DETECTION and USE_OCR:
            try:
                self.plate_reader = PlateReader(use_gpu=False)  # CPU mode to save VRAM
            except Exception as e:
                logger.warning(f"⚠️  Plate reader not initialized: {e}")
    
    def load_model(self):
        """Load YOLOv11s model"""
        try:
            device = 0 if USE_GPU else 'cpu'
            self.model = YOLO(self.model_name)
            logger.info(f"✓ Vehicle model loaded: {self.model_name}")
            return True
        except Exception as e:
            logger.error(f"✗ Failed to load vehicle model: {e}")
            return False
    
    def process(self, frame: np.ndarray, roi_polygon_points: Optional[List[List[float]]] = None) -> Dict:
        """
        Detect and classify vehicles
        
        Args:
            frame: Input BGR frame
            
        Returns:
            Dict: {
                'vehicles': [
                    {
                        'track_id': 1,
                        'vehicle_type': 'car',
                        'confidence': 0.94,
                        'bbox': [x1, y1, x2, y2],
                        'colors': [...],
                        'license_plate': {...},
                        'crop_path': '...'
                    }
                ],
                'frame_count': N
            }
        """
        if self.model is None:
            return {'vehicles': [], 'frame_count': 0}
        
        try:
            masked_frame = apply_roi_mask(frame, roi_polygon_points)

            # Run tracking
            results = self.model.track(
                masked_frame,
                persist=True,
                conf=TRACK_CONF_THRESHOLD,
                verbose=False,
                classes=list(VEHICLE_CLASSES.keys())  # Only detect vehicles
            )
            
            vehicles = []
            if results and results[0].boxes:
                for box in results[0].boxes:
                    track_id = int(box.id) if box.id is not None else -1
                    conf = float(box.conf)
                    class_id = int(box.cls)
                    
                    if conf >= CONF_THRESHOLD and track_id >= 0 and class_id in VEHICLE_CLASSES:
                        bbox = box.xyxy[0].cpu().numpy().astype(int).tolist()
                        vehicle_type = VEHICLE_CLASSES[class_id]
                        
                        # Crop vehicle region
                        crop_img = self._crop_vehicle(frame, bbox)
                        if crop_img is not None:
                            # Analyze color
                            colors = self.color_analyzer.analyze(crop_img, vehicle_type)
                            
                            # Read license plate
                            plate_info = None
                            if self.plate_reader and vehicle_type in ['car', 'truck', 'bus']:
                                plate_info = self.plate_reader.read_plate(crop_img)
                            
                            # Save crop
                            crop_path = self._save_crop(crop_img, vehicle_type, track_id)
                            
                            vehicles.append({
                                'track_id': track_id,
                                'vehicle_type': vehicle_type,
                                'confidence': conf,
                                'bbox': bbox,
                                'colors': colors or [],
                                'license_plate': plate_info or {},
                                'crop_path': crop_path
                            })
            
            return {'vehicles': vehicles, 'frame_count': len(results)}
            
        except Exception as e:
            logger.error(f"✗ Vehicle processing error: {e}")
            return {'vehicles': [], 'frame_count': 0}
    
    def _crop_vehicle(self, frame: np.ndarray, bbox: List[int]) -> Optional[np.ndarray]:
        """Crop vehicle region from frame"""
        x1, y1, x2, y2 = bbox
        h, w = frame.shape[:2]
        
        # Ensure crop is within frame
        x1 = max(0, min(x1, w))
        x2 = max(0, min(x2, w))
        y1 = max(0, min(y1, h))
        y2 = max(0, min(y2, h))
        
        if x2 <= x1 or y2 <= y1:
            return None
        
        return frame[y1:y2, x1:x2]
    
    def _save_crop(self, crop_img: np.ndarray, vehicle_type: str, track_id: int) -> str:
        """Save vehicle crop to file"""
        try:
            vehicle_dir = CROPPED_DATA_DIR / "vehicles" / vehicle_type
            vehicle_dir.mkdir(parents=True, exist_ok=True)
            
            crop_path = vehicle_dir / f"vehicle_{track_id}.jpg"
            cv2.imwrite(str(crop_path), crop_img)
            
            return crop_path.relative_to(CROPPED_DATA_DIR).as_posix()
        except Exception as e:
            logger.warning(f"⚠️  Failed to save vehicle crop: {e}")
            return ""
    
    def postprocess(self, results) -> Dict:
        """Postprocess detection results"""
        return {'vehicles': []}
