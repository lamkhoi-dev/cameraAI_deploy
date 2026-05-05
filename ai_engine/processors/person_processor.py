"""
Person Processor Module - Person Detection + Tracking + Attribute Recognition
"""

import cv2
import numpy as np
from ultralytics import YOLO
from typing import List, Dict, Optional
import logging

from ..utils.color_analyzer import ColorAnalyzer
from ..config import (
    CONF_THRESHOLD, TRACK_CONF_THRESHOLD, NUM_COLORS_PERSON,
    CROPPED_DATA_DIR, USE_GPU, GPU_DEVICE
)
from .base_processor import BaseProcessor


logger = logging.getLogger(__name__)


class PersonProcessor(BaseProcessor):
    """Person detection, tracking, and attribute recognition"""
    
    def __init__(self, model_path: str):
        """
        Args:
            model_path: Path to YOLO11s-pose model
        """
        super().__init__(model_path)
        self.color_analyzer = ColorAnalyzer(num_colors=NUM_COLORS_PERSON)
        self.tracked_persons = {}  # Dict to store track history
    
    def load_model(self):
        """Load YOLOv11s-pose model"""
        try:
            device = 0 if USE_GPU else 'cpu'
            self.model = YOLO(self.model_name)
            logger.info(f"✓ Person model loaded: {self.model_name}")
            return True
        except Exception as e:
            logger.error(f"✗ Failed to load person model: {e}")
            return False
    
    def process(self, frame: np.ndarray) -> Dict:
        """
        Detect and track persons
        
        Args:
            frame: Input BGR frame
            
        Returns:
            Dict: {
                'persons': [
                    {
                        'track_id': 1,
                        'confidence': 0.92,
                        'bbox': [x1, y1, x2, y2],
                        'keypoints': {...},
                        'attributes': {...},
                        'crop_path': '...'
                    }
                ],
                'frame_count': N
            }
        """
        if self.model is None:
            return {'persons': [], 'frame_count': 0}
        
        try:
            # Run tracking
            results = self.model.track(
                frame,
                persist=True,
                conf=TRACK_CONF_THRESHOLD,
                verbose=False
            )
            
            persons = []
            if results and results[0].boxes:
                for box in results[0].boxes:
                    track_id = int(box.id) if box.id is not None else -1
                    conf = float(box.conf)
                    
                    if conf >= CONF_THRESHOLD and track_id >= 0:
                        bbox = box.xyxy[0].cpu().numpy().astype(int).tolist()
                        
                        # Crop person region
                        crop_img = self._crop_person(frame, bbox)
                        if crop_img is not None:
                            # Analyze attributes
                            attributes = self._analyze_person(crop_img, track_id)
                            
                            # Save crop
                            crop_path = self._save_crop(crop_img, track_id)
                            
                            persons.append({
                                'track_id': track_id,
                                'confidence': conf,
                                'bbox': bbox,
                                'attributes': attributes,
                                'crop_path': crop_path
                            })
            
            return {'persons': persons, 'frame_count': len(results)}
            
        except Exception as e:
            logger.error(f"✗ Person processing error: {e}")
            return {'persons': [], 'frame_count': 0}
    
    def _crop_person(self, frame: np.ndarray, bbox: List[int]) -> Optional[np.ndarray]:
        """Crop person region from frame"""
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
    
    def _analyze_person(self, crop_img: np.ndarray, track_id: int) -> Dict:
        """Analyze person attributes (color, etc.)"""
        attributes = {
            'shirt_colors': [],
            'pants_colors': [],
            'hair_colors': []
        }
        
        try:
            h, w = crop_img.shape[:2]
            
            # Upper body (shirt) - top 50%
            if h >= 20:
                upper = crop_img[:int(h*0.5), :]
                colors = self.color_analyzer.analyze(upper, "shirt")
                if colors:
                    attributes['shirt_colors'] = colors
            
            # Lower body (pants) - bottom 50%
            if h >= 20:
                lower = crop_img[int(h*0.5):, :]
                colors = self.color_analyzer.analyze(lower, "pants")
                if colors:
                    attributes['pants_colors'] = colors
            
            # Head (hair) - top 25%
            if h >= 20:
                head = crop_img[:int(h*0.25), :]
                colors = self.color_analyzer.analyze(head, "hair")
                if colors:
                    attributes['hair_colors'] = colors
        
        except Exception as e:
            logger.warning(f"⚠️  Person attribute analysis error: {e}")
        
        return attributes
    
    def _save_crop(self, crop_img: np.ndarray, track_id: int) -> str:
        """Save person crop to file"""
        try:
            person_dir = CROPPED_DATA_DIR / "persons" / f"person_{track_id}"
            person_dir.mkdir(parents=True, exist_ok=True)
            
            crop_path = person_dir / "full_body.jpg"
            cv2.imwrite(str(crop_path), crop_img)
            
            return str(crop_path)
        except Exception as e:
            logger.warning(f"⚠️  Failed to save crop: {e}")
            return ""
    
    def postprocess(self, results) -> Dict:
        """Postprocess tracking results"""
        return {'persons': []}
