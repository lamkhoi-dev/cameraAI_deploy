"""
License Plate Reader Module - PaddleOCR Integration
"""

import re
import cv2
import numpy as np
from typing import Optional, Dict
from paddleocr import PaddleOCR


class PlateReader:
    """Đọc biển số xe sử dụng PaddleOCR (CPU mode để giải phóng GPU)"""
    
    # Vietnamese license plate regex patterns
    # Format: 29A-12345 hoặc 72C-98765 (2 số + 1 chữ + [0-1] số + 3-5 số)
    VN_PLATE_PATTERNS = [
        r'^[0-9]{2}[A-Z][0-9]?[\-\s]?[0-9]{3,5}\.?[0-9]{0,2}$',  # Standard format
        r'^[0-9]{2}[A-Z][\-\s]?[0-9]{3,5}$',                      # Without middle digit
    ]
    
    def __init__(self, use_gpu: bool = False, lang: str = "vi"):
        """
        Args:
            use_gpu: Use GPU for OCR (False = CPU mode để tiết kiệm VRAM)
            lang: Language code ('vi' for Vietnamese)
        """
        self.ocr = PaddleOCR(
            use_angle_cls=True,
            lang=lang,
            use_gpu=use_gpu,
            show_log=False
        )
    
    def read_plate(self, vehicle_crop: np.ndarray) -> Optional[Dict]:
        """
        Đọc biển số từ crop ảnh xe
        
        Args:
            vehicle_crop: BGR image of vehicle crop
            
        Returns:
            Dict: {
                'text': '29A-12345',
                'confidence': 0.87,
                'valid': True
            }
            hoặc None nếu không detect được biển số
        """
        if vehicle_crop is None or vehicle_crop.size == 0:
            return None
        
        try:
            # Preprocess: enhance contrast để OCR tốt hơn
            preprocessed = self._preprocess_image(vehicle_crop)
            
            # Extract plate region (biểu thức: 35% dưới ảnh xe)
            plate_region = self._extract_plate_region(preprocessed)
            if plate_region is None:
                return None
            
            # OCR
            ocr_result = self.ocr.ocr(plate_region, cls=True)
            if not ocr_result or not ocr_result[0]:
                return None
            
            # Combine text + get confidence
            text, confidence = self._combine_ocr_results(ocr_result)
            
            # Validate format
            cleaned_text = self._clean_text(text)
            is_valid = self._validate_format(cleaned_text)
            
            return {
                'text': cleaned_text,
                'confidence': confidence,
                'valid': is_valid
            }
            
        except Exception as e:
            print(f"⚠️  Plate reading error: {e}")
            return None
    
    def _preprocess_image(self, img: np.ndarray) -> np.ndarray:
        """Enhance image contrast để OCR tốt hơn"""
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        return enhanced
    
    def _extract_plate_region(self, img: np.ndarray) -> Optional[np.ndarray]:
        """Extract plate region từ ảnh xe"""
        h, w = img.shape[:2]
        
        # Biển số thường ở 35% dưới ảnh xe
        y_start = int(h * 0.65)
        y_end = h
        
        if y_start >= y_end or y_start < 0:
            return None
        
        plate_region = img[y_start:y_end, :]
        
        return plate_region if plate_region.size > 0 else None
    
    def _combine_ocr_results(self, ocr_result: list) -> tuple:
        """Combine OCR results from multiple lines"""
        if not ocr_result or not ocr_result[0]:
            return "", 0.0
        
        texts = []
        confidences = []
        
        for line in ocr_result[0]:
            if len(line) >= 2:
                text = line[1][0]
                conf = line[1][1]
                texts.append(text)
                confidences.append(conf)
        
        combined_text = ''.join(texts)
        avg_confidence = np.mean(confidences) if confidences else 0.0
        
        return combined_text, float(avg_confidence)
    
    def _clean_text(self, text: str) -> str:
        """Clean OCR output - remove invalid characters"""
        # Keep only alphanumeric, dash, dot
        cleaned = re.sub(r'[^A-Z0-9\-\.\s]', '', text.upper())
        # Remove extra spaces
        cleaned = ' '.join(cleaned.split())
        # Replace space with dash if needed
        cleaned = cleaned.replace(' ', '-')
        return cleaned.strip()
    
    def _validate_format(self, text: str) -> bool:
        """Validate Vietnamese license plate format"""
        for pattern in self.VN_PLATE_PATTERNS:
            if re.match(pattern, text):
                return True
        return False
