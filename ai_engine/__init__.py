"""
AI Engine - Advanced Computer Vision Processing
Supports: Person Detection + Tracking, Vehicle Detection, Fire Detection, License Plate OCR, FaceID Recognition
Optimized for Tesla P4 (8GB VRAM) with TensorRT FP16 inference
"""

__version__ = "2.0.0"
__author__ = "AI Development Team"

from .engine import AIEngine
from .processors.face_processor import FaceProcessor
from .utils.face_matcher import FaceMatchingEngine, get_face_matching_engine

__all__ = [
    "AIEngine",
    "FaceProcessor",
    "FaceMatchingEngine",
    "get_face_matching_engine"
]
