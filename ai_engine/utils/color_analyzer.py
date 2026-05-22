"""
Improved Color Analysis Module - Loại bỏ nền và noise trước phân tích
Phase 1 Optimizations: Enhanced CLAHE, stronger filtering, improved K-means convergence
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional

try:
    from ..config import (
        COLOR_MIN_SATURATION, COLOR_MIN_VALUE, COLOR_MAX_VALUE,
        COLOR_KMEANS_ITERATIONS, COLOR_KMEANS_ATTEMPTS, COLOR_KMEANS_EPSILON,
        COLOR_CLAHE_CLIPIMIT, COLOR_CLAHE_TILE_SIZE
    )
except ImportError:
    # Fallback values if config import fails
    COLOR_MIN_SATURATION = 15
    COLOR_MIN_VALUE = 25
    COLOR_MAX_VALUE = 245
    COLOR_KMEANS_ITERATIONS = 100
    COLOR_KMEANS_ATTEMPTS = 20
    COLOR_KMEANS_EPSILON = 0.1
    COLOR_CLAHE_CLIPIMIT = 3.0
    COLOR_CLAHE_TILE_SIZE = (4, 4)


class ColorAnalyzer:
    """Phân tích màu sắc với filtering nền"""
    
    # Vietnamese color names mapping
    COLOR_NAMES = {
        "red": "Đỏ",
        "orange": "Cam",
        "yellow": "Vàng",
        "yellow_green": "Vàng lục",
        "green": "Lục",
        "green_cyan": "Xanh lục",
        "cyan": "Xanh lam",
        "blue": "Xanh dương",
        "purple": "Tím",
        "pink": "Hồng",
        "magenta": "Đỏ tím",
        "black": "Đen",
        "white": "Trắng",
        "gray": "Xám"
    }
    
    def __init__(self, num_colors: int = 3, margin_ratio: float = 0.15):
        """
        Args:
            num_colors: Số lượng màu sắc chủ yếu cần detect
            margin_ratio: Tỉ lệ cắt viền để loại bỏ nền (0.15 = 15% mỗi cạnh)
        """
        self.num_colors = num_colors
        self.margin_ratio = margin_ratio
        # Phase 1 - OPTIMIZED PARAMETERS
        self.min_saturation = COLOR_MIN_SATURATION        # Improved from 10 → 15
        self.min_value = COLOR_MIN_VALUE                  # Improved from 25
        self.max_value = COLOR_MAX_VALUE                  # Improved from 245
        self.kmeans_iterations = COLOR_KMEANS_ITERATIONS  # Improved from 30 → 100
        self.kmeans_attempts = COLOR_KMEANS_ATTEMPTS      # Improved from 15 → 20
        self.kmeans_epsilon = COLOR_KMEANS_EPSILON        # NEW: Tight convergence threshold
    
    def analyze(self, crop_img: np.ndarray, part_name: str = "unknown") -> Optional[List[Dict]]:
        """
        Phân tích màu sắc của crop image - CẢI TIẾN
        
        Args:
            crop_img: Input image (BGR)
            part_name: Tên phần (hair, shirt, pants, car, etc.)
            
        Returns:
            List[Dict]: Danh sách màu sắc theo thứ tự tần suất
        """
        if crop_img is None or crop_img.size == 0:
            return None
        
        try:
            # Step 1: Crop center region để loại bỏ nền
            center_crop = self._crop_center(crop_img)
            
            # Step 1.5 (NEW): Tăng contrast bằng CLAHE
            center_crop = self._enhance_contrast(center_crop)
            
            # Step 2: Filter out extreme pixels (shadow + overexposed)
            filtered_pixels = self._filter_extreme_pixels(center_crop)
            
            if len(filtered_pixels) < 10:
                # Fallback: sử dụng tất cả pixels từ center region
                filtered_pixels = center_crop.reshape(-1, 3)
            
            # Step 3: K-means clustering (cải tiến)
            hsv_colors, bgr_colors = self._kmeans_clustering(filtered_pixels)
            
            # Step 4: Convert to color names
            color_list = []
            for rank, (hsv_color, bgr_color) in enumerate(zip(hsv_colors, bgr_colors), 1):
                color_name = self._get_color_name(hsv_color)
                r, g, b = int(bgr_color[2]), int(bgr_color[1]), int(bgr_color[0])
                
                color_list.append({
                    'rank': rank,
                    'name': color_name,
                    'rgb': (r, g, b),
                    'bgr': tuple(map(int, bgr_color)),
                    'hsv': tuple(map(int, hsv_color))
                })
            
            return color_list
            
        except Exception as e:
            print(f"⚠️  Color analysis error for {part_name}: {e}")
            return None
    
    def _crop_center(self, img: np.ndarray) -> np.ndarray:
        """Crop center region để loại bỏ viền nền"""
        h, w = img.shape[:2]
        margin_x = int(w * self.margin_ratio)
        margin_y = int(h * self.margin_ratio)
        return img[margin_y:h-margin_y, margin_x:w-margin_x]
    
    def _enhance_contrast(self, img: np.ndarray) -> np.ndarray:
        """
        Tăng contrast bằng CLAHE - PHASE 1 OPTIMIZED
        Sử dụng HSV V channel thay vì LAB L để capture colors tốt hơn
        """
        try:
            # Chuyển sang HSV color space
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            h, s, v = cv2.split(hsv)
            
            # CLAHE - OPTIMIZED PARAMETERS (Phase 1)
            # clipLimit tăng từ 2.0 → 3.0 (mạnh hơn)
            # tileGridSize giảm từ (8,8) → (4,4) (chi tiết hơn)
            clahe = cv2.createCLAHE(clipLimit=COLOR_CLAHE_CLIPIMIT, tileGridSize=COLOR_CLAHE_TILE_SIZE)
            v = clahe.apply(v)
            
            # Merge lại
            hsv = cv2.merge([h, s, v])
            result = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
            return result
        except Exception as e:
            print(f"Warning: CLAHE enhancement failed: {e}")
            return img
    
    def _filter_extreme_pixels(self, img: np.ndarray) -> np.ndarray:
        """
        Loại bỏ pixel quá tối (shadow) và quá sáng (overexposed) - PHASE 1 OPTIMIZED
        Thêm Gaussian Blur và Morphological operations để loại bỏ noise
        """
        # Step 1: Gaussian Blur để loại noise
        img_blur = cv2.GaussianBlur(img, (3, 3), 0)
        
        # Step 2: HSV filtering
        hsv = cv2.cvtColor(img_blur, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(
            hsv, 
            (0, self.min_saturation, self.min_value), 
            (179, 255, self.max_value)
        )
        filtered = img_blur[mask > 0]
        
        if len(filtered) == 0:
            return img.reshape(-1, 3)
        
        return filtered
    
    def _kmeans_clustering(self, pixels: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """K-means clustering trên filtered pixels - PHASE 1 OPTIMIZED"""
        pixels = np.float32(pixels)
        # Phase 1 OPTIMIZATIONS:
        # - iterations: 30 → 100 (better convergence)
        # - epsilon: 0.5 → 0.1 (tighter threshold)
        # - attempts: 15 → 20 (more tries for optimal solution)
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 
                   self.kmeans_iterations, self.kmeans_epsilon)
        
        _, labels, centers = cv2.kmeans(
            pixels, 
            self.num_colors, 
            None, 
            criteria, 
            self.kmeans_attempts,
            cv2.KMEANS_PP_CENTERS
        )
        
        # Sort by frequency (most frequent first)
        label_counts = np.bincount(labels.flatten())
        sorted_idx = np.argsort(-label_counts)  # Descending order
        
        centers = np.uint8(centers)
        centers_sorted = centers[sorted_idx]
        
        # Convert BGR centers to HSV for color naming
        centers_bgr = centers_sorted.reshape((self.num_colors, 1, 3))
        centers_hsv = cv2.cvtColor(centers_bgr, cv2.COLOR_BGR2HSV)
        
        return centers_hsv.reshape((self.num_colors, 3)), centers_sorted
    
    def _get_color_name(self, hsv_color: np.ndarray) -> str:
        """
        Chuyển HSV thành tên màu tiếng Việt - CẢI TIẾN
        Sử dụng thresholds tối ưu hơn
        """
        h, s, v = int(hsv_color[0]), int(hsv_color[1]), int(hsv_color[2])
        
        # Nếu saturation thấp = màu xám/trắng/đen
        if s < 20:  # Giảm từ 30 để capture pastel
            if v < 40:
                return self.COLOR_NAMES["black"]      # Đen
            elif v > 210:
                return self.COLOR_NAMES["white"]      # Trắng
            else:
                return self.COLOR_NAMES["gray"]       # Xám
        
        # Phân loại theo Hue (0-179 in OpenCV HSV)
        # Cải tiến: Ranh giới dựa trên color wheel chuẩn
        if h < 8 or h > 172:
            return self.COLOR_NAMES["red"]            # Đỏ
        elif 8 <= h < 18:
            return self.COLOR_NAMES["orange"]         # Cam
        elif 18 <= h < 28:
            return self.COLOR_NAMES["yellow"]         # Vàng
        elif 28 <= h < 38:
            return self.COLOR_NAMES["yellow_green"]   # Vàng lục
        elif 38 <= h < 75:
            return self.COLOR_NAMES["green"]          # Lục
        elif 75 <= h < 102:
            return self.COLOR_NAMES["green_cyan"]     # Xanh lục
        elif 102 <= h < 115:
            return self.COLOR_NAMES["cyan"]           # Xanh lam
        elif 115 <= h < 130:
            return self.COLOR_NAMES["blue"]           # Xanh dương
        elif 130 <= h < 148:
            return self.COLOR_NAMES["purple"]         # Tím
        elif 148 <= h < 162:
            return self.COLOR_NAMES["pink"]           # Hồng
        else:
            return self.COLOR_NAMES["magenta"]        # Đỏ tím
