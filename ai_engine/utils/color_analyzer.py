"""
Improved Color Analysis Module - Loại bỏ nền và noise trước phân tích
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional


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
    
    def analyze(self, crop_img: np.ndarray, part_name: str = "unknown") -> Optional[List[Dict]]:
        """
        Phân tích màu sắc của crop image
        
        Args:
            crop_img: Input image (BGR)
            part_name: Tên phần (hair, shirt, pants, car, etc.)
            
        Returns:
            List[Dict]: Danh sách màu sắc theo thứ tự tần suất
                [
                    {'rank': 1, 'name': 'Trắng', 'rgb': (255, 255, 255), 'bgr': (...), 'hsv': (...)},
                    {'rank': 2, 'name': 'Đen', 'rgb': (0, 0, 0), 'bgr': (...), 'hsv': (...)}
                ]
        """
        if crop_img is None or crop_img.size == 0:
            return None
        
        try:
            # Step 1: Crop center region để loại bỏ nền
            center_crop = self._crop_center(crop_img)
            
            # Step 2: Filter out very dark pixels (shadow) and overexposed pixels
            filtered_pixels = self._filter_extreme_pixels(center_crop)
            
            if len(filtered_pixels) < 10:
                # Fallback nếu filtered quá ít pixels
                filtered_pixels = center_crop.reshape(-1, 3)
            
            # Step 3: K-means clustering
            hsv_colors, bgr_colors = self._kmeans_clustering(filtered_pixels)
            
            # Step 4: Convert to color names và format output
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
    
    def _filter_extreme_pixels(self, img: np.ndarray) -> np.ndarray:
        """Loại bỏ pixel quá tối (shadow) và quá sáng (overexposed)"""
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        # HSV ranges: H(0-179), S(0-255), V(0-255)
        # Keep pixels with saturation >= 20 and value between 40-230
        mask = cv2.inRange(hsv, (0, 20, 40), (179, 255, 230))
        filtered = img[mask > 0]
        
        if len(filtered) == 0:
            return img.reshape(-1, 3)
        
        return filtered
    
    def _kmeans_clustering(self, pixels: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """K-means clustering trên filtered pixels"""
        pixels = np.float32(pixels)
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 15, 1.0)
        
        _, labels, centers = cv2.kmeans(
            pixels, 
            self.num_colors, 
            None, 
            criteria, 
            10, 
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
        """Chuyển HSV thành tên màu tiếng Việt"""
        h, s, v = int(hsv_color[0]), int(hsv_color[1]), int(hsv_color[2])
        
        # Nếu saturation thấp = màu xám/trắng/đen
        if s < 30:
            if v < 50:
                return self.COLOR_NAMES["black"]      # Đen
            elif v > 200:
                return self.COLOR_NAMES["white"]      # Trắng
            else:
                return self.COLOR_NAMES["gray"]       # Xám
        
        # Phân loại theo Hue (0-179 in OpenCV HSV)
        if h < 5 or h > 175:
            return self.COLOR_NAMES["red"]            # Đỏ
        elif 5 <= h < 15:
            return self.COLOR_NAMES["orange"]         # Cam
        elif 15 <= h < 25:
            return self.COLOR_NAMES["yellow"]         # Vàng
        elif 25 <= h < 35:
            return self.COLOR_NAMES["yellow_green"]   # Vàng lục
        elif 35 <= h < 77:
            return self.COLOR_NAMES["green"]          # Lục
        elif 77 <= h < 99:
            return self.COLOR_NAMES["green_cyan"]     # Xanh lục
        elif 99 <= h < 110:
            return self.COLOR_NAMES["cyan"]           # Xanh lam
        elif 110 <= h < 125:
            return self.COLOR_NAMES["blue"]           # Xanh dương
        elif 125 <= h < 145:
            return self.COLOR_NAMES["purple"]         # Tím
        elif 145 <= h < 165:
            return self.COLOR_NAMES["pink"]           # Hồng
        else:
            return self.COLOR_NAMES["magenta"]        # Đỏ tím
