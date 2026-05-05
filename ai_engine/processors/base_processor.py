"""
Base Processor Module - Abstract base class for all processors
"""

import numpy as np
import torch
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import logging


logger = logging.getLogger(__name__)


class BaseProcessor(ABC):
    """Abstract base class for YOLO-based processors"""
    
    def __init__(self, model_name: str, device: str = "cuda:0", use_tensorrt: bool = False):
        """
        Args:
            model_name: Model file path
            device: Device ('cuda:0', 'cpu', etc.)
            use_tensorrt: Use TensorRT engine if available
        """
        self.model_name = model_name
        self.device = device
        self.use_tensorrt = use_tensorrt
        self.model = None
    
    @abstractmethod
    def load_model(self):
        """Load YOLO model"""
        pass
    
    @abstractmethod
    def process(self, frame: np.ndarray) -> Dict:
        """
        Process frame and return results
        
        Args:
            frame: Input BGR frame
            
        Returns:
            Dict: Processing results (format depends on processor type)
        """
        pass
    
    @abstractmethod
    def postprocess(self, results) -> Dict:
        """
        Postprocess model outputs
        
        Args:
            results: Raw model outputs
            
        Returns:
            Dict: Formatted results
        """
        pass
    
    def _check_gpu_available(self) -> bool:
        """Check if GPU is available"""
        return torch.cuda.is_available()
    
    def _get_optimal_device(self) -> str:
        """Get optimal device for inference"""
        if self._check_gpu_available():
            return "cuda:0"
        return "cpu"
    
    def unload_model(self):
        """Unload model from memory"""
        if self.model:
            del self.model
            self.model = None
            torch.cuda.empty_cache()
