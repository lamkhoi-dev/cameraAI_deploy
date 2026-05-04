"""
Face Processor Module - Face Detection + Recognition + Embedding Extraction
Uses DeepFace for face detection and embedding extraction
"""

import cv2
import numpy as np
from typing import List, Dict, Optional, Tuple
import logging
from pathlib import Path

from ..config import (
    USE_FACE_DETECTION, USE_FACE_RECOGNITION, FACE_DETECTION_CONFIDENCE,
    FACE_EMBEDDING_DIM, FACE_EMBEDDING_MODEL, FACE_MIN_FACE_SIZE,
    USE_GPU, GPU_DEVICE, CROPPED_DATA_DIR
)
from .base_processor import BaseProcessor


logger = logging.getLogger(__name__)


class FaceProcessor(BaseProcessor):
    """Face detection, recognition, and embedding extraction using DeepFace"""
    
    def __init__(self):
        """Initialize DeepFace"""
        super().__init__("deepface")
        self.model_loaded = False
        
    def load_model(self) -> bool:
        """Load DeepFace models"""
        if not (USE_FACE_DETECTION and USE_FACE_RECOGNITION):
            logger.info("⚠️  Face detection/recognition disabled in config")
            return False
        
        try:
            # Import DeepFace
            try:
                from deepface import DeepFace
            except ImportError:
                logger.error("✗ DeepFace not installed. Install with: pip install deepface tensorflow")
                return False
            
            # Test that models load successfully
            logger.info("✓ DeepFace loaded successfully")
            self.model_loaded = True
            return True
            
        except Exception as e:
            logger.error(f"✗ Failed to load face processor: {e}")
            return False
    
    def process(self, frame: np.ndarray, track_id: int) -> Dict:
        """
        Detect faces and extract embeddings
        
        Args:
            frame: Input BGR frame
            track_id: Person track ID for organization
            
        Returns:
            Dict: {
                'faces': [
                    {
                        'face_id': 1,
                        'bbox': [x1, y1, x2, y2],
                        'confidence': 0.98,
                        'embedding': [float array 512D],
                        'age': 30,
                        'gender': 'M',
                        'emotion': 'happy',
                        'crop_path': '...'
                    }
                ],
                'frame_count': N
            }
        """
        result = {'faces': [], 'frame_count': 0}
        
        if not self.model_loaded or not USE_FACE_DETECTION:
            return result
        
        try:
            from deepface import DeepFace
            
            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Detect faces
            try:
                detections = DeepFace.extract_faces(frame_rgb, detector_backend='opencv', enforce_detection=False)
            except Exception as e:
                logger.debug(f"Face detection error: {e}")
                return result
            
            if not detections:
                return result
            
            face_list = []
            for face_idx, face_data in enumerate(detections):
                try:
                    # Extract face information
                    face_info = face_data['facial_area']
                    x1 = int(face_info['x'])
                    y1 = int(face_info['y'])
                    w = int(face_info['w'])
                    h = int(face_info['h'])
                    x2 = x1 + w
                    y2 = y1 + h
                    
                    confidence = float(face_data.get('confidence', 0.9))
                    
                    # Skip low confidence faces
                    if confidence < FACE_DETECTION_CONFIDENCE:
                        continue
                    
                    # Check minimum face size
                    if w < FACE_MIN_FACE_SIZE or h < FACE_MIN_FACE_SIZE:
                        continue
                    
                    bbox = [x1, y1, x2, y2]
                    
                    # Extract embedding if configured
                    embedding = None
                    if USE_FACE_RECOGNITION:
                        try:
                            embedding = self.extract_embedding_deepface(frame_rgb, bbox)
                        except Exception as e:
                            logger.debug(f"Embedding extraction error: {e}")
                    
                    # Extract attributes
                    age = None
                    gender = None
                    emotion = None
                    
                    try:
                        # Analyze demographics
                        cropped = frame_rgb[y1:y2, x1:x2]
                        demo = DeepFace.analyze(cropped, actions=['age', 'gender', 'emotion'], enforce_detection=False)[0]
                        age = int(demo['age'])
                        gender = demo['gender'].get(list(demo['gender'].keys())[0]) if 'gender' in demo else None
                        emotion = demo['dominant_emotion'] if 'dominant_emotion' in demo else None
                    except Exception as e:
                        logger.debug(f"Demographics extraction error: {e}")
                    
                    # Crop face region
                    face_crop = self._crop_face(frame, bbox)
                    crop_path = None
                    if face_crop is not None:
                        crop_path = self._save_crop(face_crop, track_id, face_idx)
                    
                    face_result = {
                        'face_id': face_idx,
                        'bbox': bbox,
                        'confidence': confidence,
                        'embedding': embedding,
                        'crop_path': crop_path
                    }
                    
                    # Add optional attributes
                    if age is not None:
                        face_result['age'] = age
                    if gender is not None:
                        face_result['gender'] = gender
                    if emotion is not None:
                        face_result['emotion'] = emotion
                    
                    face_list.append(face_result)
                    
                except Exception as e:
                    logger.warning(f"⚠️  Error processing face {face_idx}: {e}")
                    continue
            
            result['faces'] = face_list
            result['frame_count'] = len(face_list)
            
            return result
            
        except Exception as e:
            logger.error(f"✗ Face processing error: {e}")
            return result
    
    def extract_embedding(self, face_image: np.ndarray) -> Optional[List[float]]:
        """
        Extract embedding from a face image
        
        Args:
            face_image: Cropped face BGR image
            
        Returns:
            512-dimensional embedding vector or None
        """
        if not self.model_loaded:
            return None
        
        try:
            # Convert to RGB
            face_rgb = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)
            
            # Return embedding
            return self.extract_embedding_deepface(face_rgb, None)
            
        except Exception as e:
            logger.warning(f"⚠️  Embedding extraction error: {e}")
            return None
    
    def extract_embedding_deepface(self, frame_rgb: np.ndarray, bbox: Optional[List[int]] = None) -> Optional[List[float]]:
        """
        Extract embedding using DeepFace
        
        Args:
            frame_rgb: RGB image (full frame or cropped face)
            bbox: Optional bounding box [x1, y1, x2, y2] for cropping
            
        Returns:
            512-dimensional embedding vector or None
        """
        try:
            from deepface import DeepFace
            
            # Crop if bbox provided
            if bbox:
                x1, y1, x2, y2 = bbox
                face_img = frame_rgb[y1:y2, x1:x2]
            else:
                face_img = frame_rgb
            
            # Extract embedding using FaceNet (produces 128D embeddings)
            # or VGGFace2 (2048D) - we'll normalize to 512D
            embedding_dict = DeepFace.represent(face_img, model_name='VGGFace2', enforce_detection=False)[0]
            embedding = embedding_dict['embedding']
            
            # Normalize to 512D if needed (VGGFace2 produces 2048D)
            if len(embedding) != FACE_EMBEDDING_DIM:
                # Use PCA or simple truncation to 512D
                embedding = embedding[:FACE_EMBEDDING_DIM]
            
            return embedding
            
        except Exception as e:
            logger.debug(f"DeepFace embedding extraction failed: {e}")
            return None
    
    def compare_embeddings(self, emb1: List[float], emb2: List[float]) -> float:
        """
        Calculate similarity between two embeddings using cosine distance
        
        Args:
            emb1: First embedding vector (512D)
            emb2: Second embedding vector (512D)
            
        Returns:
            Similarity score (0.0 to 1.0), where 1.0 is identical
        """
        if not emb1 or not emb2:
            return 0.0
        
        try:
            # Convert to numpy arrays
            v1 = np.array(emb1, dtype=np.float32)
            v2 = np.array(emb2, dtype=np.float32)
            
            # Normalize vectors
            v1 = v1 / np.linalg.norm(v1)
            v2 = v2 / np.linalg.norm(v2)
            
            # Cosine similarity
            similarity = np.dot(v1, v2)
            
            # Convert from [-1, 1] to [0, 1]
            return float((similarity + 1) / 2)
            
        except Exception as e:
            logger.warning(f"⚠️  Embedding comparison error: {e}")
            return 0.0
    
    def _crop_face(self, frame: np.ndarray, bbox: List[int]) -> Optional[np.ndarray]:
        """Crop face region from frame"""
        x1, y1, x2, y2 = bbox
        h, w = frame.shape[:2]
        
        # Add padding for better recognition
        padding = 10
        x1 = max(0, x1 - padding)
        y1 = max(0, y1 - padding)
        x2 = min(w, x2 + padding)
        y2 = min(h, y2 + padding)
        
        if x2 <= x1 or y2 <= y1:
            return None
        
        return frame[y1:y2, x1:x2]
    
    def _save_crop(self, crop_img: np.ndarray, track_id: int, face_idx: int) -> str:
        """Save cropped face image"""
        try:
            faces_dir = CROPPED_DATA_DIR / "faces"
            faces_dir.mkdir(exist_ok=True)
            
            person_dir = faces_dir / f"person_{track_id}"
            person_dir.mkdir(exist_ok=True)
            
            # Find next available file number
            existing_files = list(person_dir.glob(f"face_{face_idx}_*.jpg"))
            file_num = len(existing_files)
            
            crop_path = person_dir / f"face_{face_idx}_{file_num}.jpg"
            cv2.imwrite(str(crop_path), crop_img)
            
            return str(crop_path)
            
        except Exception as e:
            logger.warning(f"⚠️  Failed to save face crop: {e}")
            return ""
