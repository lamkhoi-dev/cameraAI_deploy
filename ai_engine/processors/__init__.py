"""Processors package"""

from .base_processor import BaseProcessor
from .person_processor import PersonProcessor
from .vehicle_processor import VehicleProcessor
from .fire_processor import FireProcessor
from .face_processor import FaceProcessor

__all__ = [
    "BaseProcessor",
    "PersonProcessor",
    "VehicleProcessor",
    "FireProcessor",
    "FaceProcessor"
]
