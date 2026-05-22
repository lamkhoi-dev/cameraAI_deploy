# 🚀 ĐỀ XUẤT CẢI THIỆN CAMERA-TRACKING-AI

**Ngày**: May 15, 2026  
**Mục tiêu**: Tăng tỷ lệ nhận diện màu sắc → Giảm frame → Tối ưu độ phân giải → Cải thiện OCR biển số

---

## 📋 NỘI DUNG

1. [Tăng tỷ lệ nhận diện màu sắc](#1-tăng-tỷ-lệ-nhận-diện-chính-xác-màu-sắc)
2. [Giảm frame từ 1s → 3-5 frame](#2-giảm-frame---từ-1s--3-5-frame)
3. [Tăng độ phân giải & tối ưu](#3-tăng-độ-phân-giải--độ-chính-xác---tối-ưu)
4. [Tăng độ chính xác nhận diện biển số](#4-tăng-độ-chính-xác-nhận-diện-biển-số)
5. [Bảng ưu tiên](#-bảng-tómlại---ưtiên-theo-impact)
6. [Lợi ích dự kỳ](#-lợi-ích-dự-kỳ-sau-các-cải-tiến)

---

## 1. Tăng tỷ lệ nhận diện chính xác màu sắc

### 📌 Vấn đề hiện tại
- K-means clustering chỉ dùng 3-10 màu → có thể thiếu chi tiết
- CLAHE chỉ áp dụng trên channel L (LAB) → chưa tối ưu
- Hue thresholds có thể không chính xác với ánh sáng thay đổi
- Chưa xử lý noise từ bóng/phản quang

### ✅ Các đề xuất cải tiến

#### a) Nâng cấp phương pháp phân tích màu (Hierarchical K-means)
**File**: `ai_engine/utils/color_analyzer.py`

```python
# Cải tiến:
# Thay K-means thuần thành Hierarchical K-means
# Vòng 1: Cluster thành 5 màu chính
# Vòng 2: Cluster riêng từng nhóm thành 2-3 màu con
# Lợi ích: Capture các màu tương tự (đỏ sẫm vs đỏ nhạt)

def _hierarchical_kmeans(self, pixels: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Hierarchical K-means clustering
    - Stage 1: Cluster thành 5 màu chính
    - Stage 2: Cluster riêng mỗi nhóm thành 2-3 màu
    """
    # Stage 1: Phân loại thô thành 5 nhóm
    pixels = np.float32(pixels)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 50, 0.1)
    
    _, labels1, centers1 = cv2.kmeans(
        pixels, 5, None, criteria, 20, cv2.KMEANS_PP_CENTERS
    )
    
    # Stage 2: Phân loại chi tiết mỗi nhóm
    final_centers = []
    for i in range(5):
        group_pixels = pixels[labels1.flatten() == i]
        if len(group_pixels) > 10:
            _, _, centers2 = cv2.kmeans(
                group_pixels, 2, None, criteria, 10, cv2.KMEANS_PP_CENTERS
            )
            final_centers.extend(centers2)
    
    return np.array(final_centers)
```

---

#### b) Cải tiến CLAHE (Contrast Limited Adaptive Histogram Equalization)
**File**: `ai_engine/utils/color_analyzer.py:_enhance_contrast()`

```python
# Cải tiến so với hiện tại:
# - Áp dụng CLAHE trên HSV channel V (brightness) thay LAB
# - Tăng clipLimit từ 2.0 → 3.0 (mạnh hơn)
# - Giảm tileGridSize từ (8,8) → (4,4) (chi tiết hơn)

def _enhance_contrast(self, img: np.ndarray) -> np.ndarray:
    """
    Tăng contrast bằng CLAHE - CẢI TIẾN
    Áp dụng trên HSV V channel thay vì LAB L
    """
    try:
        # Chuyển sang HSV color space
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        
        # CLAHE - cải tiến parameters
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(4, 4))
        v = clahe.apply(v)
        
        # Merge lại
        hsv = cv2.merge([h, s, v])
        result = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        return result
    except Exception as e:
        print(f"Warning: CLAHE enhancement failed: {e}")
        return img
```

---

#### c) Lọc nhiễu tốt hơn (Morphological operations)
**File**: `ai_engine/utils/color_analyzer.py:_filter_extreme_pixels()`

```python
# Thêm:
# - Gaussian Blur (kernel 3x3) trước phân tích
# - Morphological operations (Open+Close) để loại bỏ pixel lẻ
# - Tăng min_saturation từ 10 → 15

def _filter_extreme_pixels(self, img: np.ndarray) -> np.ndarray:
    """Loại bỏ pixel quá tối (shadow) và quá sáng (overexposed) - CẢI TIẾN"""
    
    # Bước 1: Gaussian Blur để loại noise
    img_blur = cv2.GaussianBlur(img, (3, 3), 0)
    
    # Bước 2: Morphological operations
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    img_morph = cv2.morphologyEx(img_blur, cv2.MORPH_OPEN, kernel, iterations=1)
    img_morph = cv2.morphologyEx(img_morph, cv2.MORPH_CLOSE, kernel, iterations=1)
    
    # Bước 3: HSV filtering
    hsv = cv2.cvtColor(img_morph, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(
        hsv, 
        (0, 15, self.min_value),  # Tăng saturation min từ 10 → 15
        (179, 255, self.max_value)
    )
    filtered = img_morph[mask > 0]
    
    if len(filtered) == 0:
        return img.reshape(-1, 3)
    
    return filtered
```

---

#### d) Động hóa thresholds dựa trên histogram
**File**: `ai_engine/utils/color_analyzer.py` (mới method)

```python
def _auto_adjust_thresholds(self, img: np.ndarray) -> None:
    """
    Tự động điều chỉnh min_value/max_value dựa trên histogram
    Lợi ích: Tích ứng với điều kiện ánh sáng thay đổi
    """
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    v_channel = hsv[:, :, 2]
    
    # Tính histogram của V channel
    hist = cv2.calcHist([v_channel], [0], None, [256], [0, 256])
    median_brightness = np.where(np.cumsum(hist) >= hist.sum() * 0.5)[0][0]
    
    # Điều chỉnh động
    if median_brightness < 80:  # Ảnh tối
        self.min_value = 15
        self.max_value = 230
    elif median_brightness > 180:  # Ảnh sáng
        self.min_value = 40
        self.max_value = 255
    else:  # Ảnh bình thường
        self.min_value = 25
        self.max_value = 245
```

---

#### e) Tăng K-means convergence
**File**: `ai_engine/utils/color_analyzer.py:__init__()`

```python
# Cập nhật __init__:
self.kmeans_iterations = 100  # Tăng từ 30
self.kmeans_attempts = 20     # Tăng từ 15
self.kmeans_epsilon = 0.1     # Giảm từ 0.5 để hội tụ chặt

# Cập nhật _kmeans_clustering:
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 
           self.kmeans_iterations, self.kmeans_epsilon)  # 0.1 thay vì 0.5
```

---

#### f) Thêm Delta E (CIE L*a*b*) để so sánh màu
**File**: `ai_engine/utils/color_analyzer.py` (mới method)

```python
def _calculate_delta_e(self, lab1: np.ndarray, lab2: np.ndarray) -> float:
    """
    Tính khoảng cách màu trong không gian LAB (Delta E)
    Lợi ích: Khớp với cách con mắt nhìn (perceptually accurate)
    """
    delta_l = lab1[0] - lab2[0]
    delta_a = lab1[1] - lab2[1]
    delta_b = lab1[2] - lab2[2]
    
    delta_e = np.sqrt(delta_l**2 + delta_a**2 + delta_b**2)
    return delta_e

def _merge_similar_colors(self, colors_bgr: np.ndarray, threshold: float = 15.0) -> np.ndarray:
    """
    Merge các màu tương tự dựa trên Delta E
    """
    colors_lab = []
    for bgr in colors_bgr:
        bgr_reshaped = np.uint8([[[bgr[0], bgr[1], bgr[2]]]]])
        lab = cv2.cvtColor(bgr_reshaped, cv2.COLOR_BGR2LAB)
        colors_lab.append(lab[0][0])
    
    colors_lab = np.array(colors_lab)
    merged = []
    used = set()
    
    for i, color in enumerate(colors_lab):
        if i in used:
            continue
        merged.append(colors_bgr[i])
        for j in range(i+1, len(colors_lab)):
            if j not in used:
                delta_e = self._calculate_delta_e(color, colors_lab[j])
                if delta_e < threshold:
                    used.add(j)
    
    return np.array(merged)
```

---

## 2. Giảm frame - từ 1s → 3-5 frame

### 📌 Vấn đề hiện tại
- `SKIP_FRAMES` trong `config.py` = 3 (xử lý ~10 fps)
- `SKIP_FRAMES` trong `main.py` = 1 (xử lý ~30 fps)
- Không nhất quán → cần tối ưu

### ✅ Các đề xuất cải tiến

#### a) Thống nhất SKIP_FRAMES
**File**: `ai_engine/config.py` và `main.py`

```python
# Trong config.py - thay đổi:
SKIP_FRAMES = 5  # Xử lý 1 frame / 5 frame = ~6 fps (giảm 80% tính toán)

# Trong main.py - sử dụng config.SKIP_FRAMES thay vì hardcode
```

**Lợi ích**:
- Giảm từ 30 fps xuống 6 fps = tiết kiệm 80% tính toán GPU
- Vẫn đủ độ chính xác cho tracking/color analysis
- Giảm bớt beləy, cấu hình tập trung

---

#### b) Adaptive frame skipping
**File**: `ai_engine/engine.py` (thêm logic mới)

```python
def _get_adaptive_skip_frames(self) -> int:
    """
    Động điều chỉnh SKIP_FRAMES dựa trên GPU utilization
    """
    if not self.use_gpu:
        return SKIP_FRAMES
    
    try:
        import pynvml
        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(GPU_DEVICE)
        
        util = pynvml.nvmlDeviceGetUtilizationRates(handle)
        gpu_util = util.gpu
        
        if gpu_util < 60:
            return 3  # Xử lý nhiều hơn
        elif gpu_util > 85:
            return 7  # Xử lý ít hơn
        else:
            return 5  # Balanced
            
    except Exception as e:
        logger.warning(f"GPU monitoring failed: {e}")
        return SKIP_FRAMES

# Trong process loop:
frame_idx += 1
if frame_idx % self._get_adaptive_skip_frames() == 0:
    # Process frame
    pass
```

---

#### c) Ghi nhớ tracking giữa skip frames (Multi-frame tracking)
**File**: `ai_engine/processors/person_processor.py` + `vehicle_processor.py`

```python
class PersonProcessor(BaseProcessor):
    def __init__(self, model_path: str):
        super().__init__(model_path)
        self.track_history = {}  # Lưu vị trí trước đó
        self.skip_frames_buffer = 2  # Dự đoán 2 frame
    
    def _predict_next_position(self, track_id: int, prev_bbox: list) -> list:
        """
        Dự đoán vị trí object trong skip frames
        """
        if track_id not in self.track_history:
            return prev_bbox
        
        prev_prev_bbox = self.track_history[track_id]
        
        # Linear extrapolation
        dx = prev_bbox[0] - prev_prev_bbox[0]
        dy = prev_bbox[1] - prev_prev_bbox[1]
        
        predicted_bbox = [
            prev_bbox[0] + dx * self.skip_frames_buffer,
            prev_bbox[1] + dy * self.skip_frames_buffer,
            prev_bbox[2] + dx * self.skip_frames_buffer,
            prev_bbox[3] + dy * self.skip_frames_buffer
        ]
        
        return predicted_bbox
    
    def process(self, frame: np.ndarray, is_skipped: bool = False) -> Dict:
        """
        is_skipped = True: Sử dụng predicted positions
        is_skipped = False: Thực hiện detection
        """
        if is_skipped:
            # Xử lý frame skip - dùng predicted positions
            predicted_persons = []
            for track_id, prev_bbox in self.track_history.items():
                predicted_bbox = self._predict_next_position(track_id, prev_bbox)
                predicted_persons.append({
                    'track_id': track_id,
                    'bbox': predicted_bbox,
                    'confidence': 0.95,  # High confidence cho predicted
                    'predicted': True
                })
            return {'persons': predicted_persons, 'frame_count': 0}
        else:
            # Xử lý frame thực - thực hiện detection
            results = self.model.track(frame, persist=True, conf=TRACK_CONF_THRESHOLD)
            # ... normal processing
            self.track_history = {p['track_id']: p['bbox'] for p in persons}
```

---

## 3. Tăng độ phân giải & độ chính xác - tối ưu

### 📌 Vấn đề hiện tại
- `FRAME_RESIZE_SCALE` = 1.0 (full resolution) → GPU pressure cao
- Chưa dùng TensorRT → model chạy pure PyTorch → chậm
- Model input 640x640 có thể quá nhỏ cho chi tiết màu

### ✅ Các đề xuất cải tiến

#### a) Kích hoạt TensorRT
**File**: `ai_engine/config.py`

```python
# Cập nhật config:
USE_TENSORRT = True   # Thay vì False
USE_FP16 = True       # Giữ nguyên
USE_INT8 = False      # Giữ nguyên

# Export commands (chạy 1 lần):
# python -c "
# from ultralytics import YOLO
# model = YOLO('yolo11s-pose.pt')
# model.export(format='engine', half=True)
# model = YOLO('yolo11s.pt')
# model.export(format='engine', half=True)
# "

# Sau export, cập nhật model paths:
MODELS = {
    'person_pose': {
        'name': 'yolo11s-pose.engine',  # Thay .pt → .engine
        ...
    },
    'vehicle': {
        'name': 'yolo11s.engine',  # Thay .pt → .engine
        ...
    }
}
```

**Lợi ích**:
- 2-3x tốc độ inference
- Tiết kiệm VRAM 30-40%
- Độ chính xác vẫn 99%+

---

#### b) FP16 precision (đã có, xác nhận)
**File**: `ai_engine/config.py`

```python
USE_FP16 = True  # Model nhẹ 50%, độ chính xác vẫn 99%+
```

---

#### c) Multi-scale inference
**File**: `ai_engine/engine.py` (mới logic)

```python
def process_frame(self, frame, camera_id: str, frame_idx: int) -> Dict:
    """
    Multi-scale inference:
    - Scale 1 (640x640): Phát hiện objects to (toàn bộ frame)
    - Scale 2 (1280x1280): Chi tiết (crops của objects)
    """
    
    # Scale 1: Phát hiện tổng quát
    scale1_results = self.person_processor.process(frame)
    
    # Scale 2: Chi tiết trên crops
    refined_persons = []
    for person in scale1_results['persons']:
        x1, y1, x2, y2 = person['bbox']
        crop = frame[y1:y2, x1:x2]
        
        # Upsample crop để có chi tiết tốt hơn
        crop_large = cv2.resize(crop, (min(crop.shape[1]*2, 1280), 
                                       min(crop.shape[0]*2, 1280)))
        
        # Analyze chi tiết (màu, pose)
        person['colors'] = self.color_analyzer.analyze(crop_large)
        
        refined_persons.append(person)
    
    return {
        'persons': refined_persons,
        'vehicles': self.vehicle_processor.process(frame)['vehicles']
    }
```

---

#### d) Dynamic resolution
**File**: `ai_engine/engine.py` (mới logic)

```python
def _get_optimal_input_size(self, object_count: int) -> int:
    """
    Điều chỉnh input size dựa trên số objects detected
    """
    if object_count < 3:
        return 480   # Nhanh
    elif object_count < 8:
        return 640   # Balanced
    else:
        return 768   # Chính xác

# Sử dụng:
optimal_size = self._get_optimal_input_size(len(detected_objects))
results = model(frame, imgsz=optimal_size)
```

---

#### e) Upsampling crops nhỏ
**File**: `ai_engine/utils/color_analyzer.py:analyze()`

```python
def analyze(self, crop_img: np.ndarray, part_name: str = "unknown") -> Optional[List[Dict]]:
    """
    Phân tích màu với xử lý upsampling cho crops nhỏ
    """
    if crop_img is None or crop_img.size == 0:
        return None
    
    # Upsampling nếu crop quá nhỏ
    h, w = crop_img.shape[:2]
    if h < 64 or w < 64:
        crop_img = cv2.resize(crop_img, (128, 128), interpolation=cv2.INTER_CUBIC)
        # Áp dụng CLAHE mạnh hơn
        clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(4, 4))
        # ... apply CLAHE
    
    # Tiếp tục phân tích...
    center_crop = self._crop_center(crop_img)
    center_crop = self._enhance_contrast(center_crop)
    # ...
```

---

## 4. Tăng độ chính xác nhận diện biển số

### 📌 Vấn đề hiện tại
- PaddleOCR accuracy ~85-90% (không tối ưu)
- Preprocessing chỉ cơ bản
- Không có post-processing logic

### ✅ Các đề xuất cải tiến

#### a) Cải tiến preprocessing
**File**: `ai_engine/utils/plate_reader.py:_preprocess_image()`

```python
def _preprocess_image(self, img: np.ndarray) -> np.ndarray:
    """
    Enhance image contrast để OCR tốt hơn - CẢI TIẾN
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Step 1: Bilateral Filter (noise removal mà không blur edge)
    filtered = cv2.bilateralFilter(gray, 9, 75, 75)
    
    # Step 2: CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(4, 4))
    enhanced = clahe.apply(filtered)
    
    # Step 3: Morphological operations (dilate text)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    enhanced = cv2.dilate(enhanced, kernel, iterations=1)
    
    # Step 4: Thresholding để tách text từ background
    _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    return binary
```

---

#### b) Multi-stage OCR
**File**: `ai_engine/utils/plate_reader.py:read_plate()`

```python
def read_plate(self, vehicle_crop: np.ndarray) -> Optional[Dict]:
    """
    Multi-stage OCR với fallback
    """
    if vehicle_crop is None or vehicle_crop.size == 0:
        return None
    
    try:
        preprocessed = self._preprocess_image(vehicle_crop)
        plate_region = self._extract_plate_region(preprocessed)
        
        if plate_region is None:
            return None
        
        # Stage 1: PaddleOCR standard
        ocr_result = self.ocr.ocr(plate_region, cls=True)
        text1, confidence1 = self._combine_ocr_results(ocr_result)
        
        # Stage 2: Nếu confidence thấp, thử EasyOCR
        if confidence1 < 0.80:
            try:
                import easyocr
                reader = easyocr.Reader(['en'])
                result2 = reader.readtext(plate_region)
                text2 = ''.join([r[1] for r in result2])
                confidence2 = np.mean([r[2] for r in result2])
                
                if confidence2 > confidence1:
                    text1, confidence1 = text2, confidence2
            except Exception as e:
                logger.warning(f"EasyOCR fallback failed: {e}")
        
        # Stage 3: Format matching (regex voting)
        cleaned_text = self._clean_text(text1)
        is_valid = self._validate_format(cleaned_text)
        
        # Nếu vẫn không hợp lệ, cố sửa
        if not is_valid:
            cleaned_text = self._auto_correct_format(cleaned_text)
        
        return {
            'text': cleaned_text,
            'confidence': confidence1,
            'valid': is_valid or self._validate_format(cleaned_text)
        }
        
    except Exception as e:
        logger.error(f"Plate reading error: {e}")
        return None
```

---

#### c) Format validation hacker
**File**: `ai_engine/utils/plate_reader.py` (mới method)

```python
def _auto_correct_format(self, text: str) -> str:
    """
    Cố gắng sửa OCR output để khớp với định dạng VN
    Format VN: 29A-12345 hoặc 72C-98765
    """
    import difflib
    
    # Lưu trữ các định dạng chuẩn
    valid_patterns = [
        r'^[0-9]{2}[A-Z][0-9]?[\-\s]?[0-9]{3,5}\.?[0-9]{0,2}$',
        r'^[0-9]{2}[A-Z][\-\s]?[0-9]{3,5}$',
    ]
    
    text = text.upper()
    
    # Cố gắng sửa bằng fuzzy matching
    # Ví dụ: "291-12345" → "29A-12345"
    possibilities = []
    
    # Xử lý từng phần
    if len(text) >= 5:
        part1 = text[:3]  # "291"
        part2 = text[3:]  # "-12345"
        
        # Sửa part 1
        if part1[2].isdigit() and part1[2] in '01':
            # Có thể '0' hoặc '1' được OCR thành chữ 'O' hoặc 'I'
            possible_letters = ['O', 'I', 'L']
            for letter in possible_letters:
                corrected = part1[:2] + letter + part2
                if self._validate_format(corrected):
                    possibilities.append((corrected, 0.75))
    
    return max(possibilities, key=lambda x: x[1])[0] if possibilities else text
```

---

#### d) Lưu confidence từng ký tự
**File**: `ai_engine/utils/plate_reader.py` (mới method)

```python
def _ocr_per_character(self, plate_region: np.ndarray) -> Dict:
    """
    OCR từng ký tự riêng, ghi lại confidence
    """
    char_results = []
    
    # Chia plate thành grid cells
    h, w = plate_region.shape[:2]
    cell_width = w // 8  # Giả sử 8 ký tự
    
    for i in range(8):
        x_start = i * cell_width
        x_end = (i + 1) * cell_width
        cell = plate_region[:, x_start:x_end]
        
        # OCR cell này
        ocr_result = self.ocr.ocr(cell, cls=True)
        if ocr_result and ocr_result[0]:
            char = ocr_result[0][0][1][0]
            confidence = ocr_result[0][0][1][1]
            char_results.append({
                'position': i,
                'char': char,
                'confidence': confidence,
                'needs_review': confidence < 0.70
            })
    
    return char_results
```

---

#### e) Plate detection model
**File**: `ai_engine/processors/vehicle_processor.py`

```python
class VehicleProcessor(BaseProcessor):
    def __init__(self, model_path: str):
        super().__init__(model_path)
        
        # Thêm plate detection model
        self.plate_detector = None
        if os.path.exists('ai_engine/models/yolo11n-plate.pt'):
            try:
                self.plate_detector = YOLO('ai_engine/models/yolo11n-plate.pt')
                logger.info("✓ Plate detection model loaded")
            except Exception as e:
                logger.warning(f"⚠️  Plate detector not loaded: {e}")
    
    def _detect_plate_region(self, vehicle_crop: np.ndarray) -> Optional[np.ndarray]:
        """
        Phát hiện vùng biển số trong crop xe
        """
        if self.plate_detector is None:
            # Fallback: crop phần dưới (35%)
            h = vehicle_crop.shape[0]
            return vehicle_crop[int(h*0.65):, :]
        
        try:
            results = self.plate_detector(vehicle_crop)
            if results and results[0].boxes:
                box = results[0].boxes[0]
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                return vehicle_crop[y1:y2, x1:x2]
        except Exception as e:
            logger.warning(f"Plate detection failed: {e}")
        
        return None
```

---

#### f) Temporal validation
**File**: `ai_engine/processors/vehicle_processor.py` (mới logic)

```python
class VehicleProcessor(BaseProcessor):
    def __init__(self, model_path: str):
        super().__init__(model_path)
        self.plate_history = {}  # Lưu lịch sử biển số
    
    def _validate_plate_temporal(self, track_id: int, current_plate: str, confidence: float) -> Dict:
        """
        Confirm plate khi ≥3 frame liên tiếp khớp
        """
        if track_id not in self.plate_history:
            self.plate_history[track_id] = []
        
        self.plate_history[track_id].append({
            'plate': current_plate,
            'confidence': confidence,
            'frame': time.time()
        })
        
        # Giữ chỉ 10 frame gần nhất
        if len(self.plate_history[track_id]) > 10:
            self.plate_history[track_id] = self.plate_history[track_id][-10:]
        
        # Voting logic
        plates = [p['plate'] for p in self.plate_history[track_id][-5:]]
        plate_counts = {}
        for plate in plates:
            plate_counts[plate] = plate_counts.get(plate, 0) + 1
        
        most_common_plate = max(plate_counts.items(), key=lambda x: x[1])[0]
        vote_count = plate_counts[most_common_plate]
        
        return {
            'plate': most_common_plate,
            'confidence': confidence,
            'confirmed': vote_count >= 3  # Confirm nếu ≥3 frame khớp
        }
```

---

#### g) Xử lý crops nhỏ
**File**: `ai_engine/utils/plate_reader.py`

```python
def _preprocess_image(self, img: np.ndarray) -> np.ndarray:
    """
    Xử lý crops nhỏ bằng upsampling
    """
    h, w = img.shape[:2]
    
    # Upsampling nếu crop quá nhỏ
    if h < 64 or w < 64:
        img = cv2.resize(img, (256, max(64, int(256 * h / w))), 
                        interpolation=cv2.INTER_CUBIC)
        # Apply Unsharp Mask để làm sắc nét text
        img = cv2.GaussianBlur(img, (0, 0), 2.0)
        img = cv2.addWeighted(img, 2.0, cv2.GaussianBlur(img, (0, 0), 2.0), -1.0, 0)
    
    # ... tiếp tục preprocessing bình thường
```

---

## 📊 Bảng tómlại - ưu tiên theo impact

| Độ ưu tiên | Cải tiến | Impact | Khó độ | Thời gian |
|-----------|---------|--------|-------|----------|
| 🔴 **CẤP 1** | TensorRT export | ⚡⚡⚡ (3x nhanh) | Dễ | 30 phút |
| 🔴 **CẤP 1** | Tối ưu CLAHE thresholds | ⚡⚡ (màu +15-20%) | Dễ | 20 phút |
| 🟠 **CẤP 2** | Plate detection + temporal validation | ⚡⚡⚡ (biển số 95%+) | Trung bình | 2-3 giờ |
| 🟠 **CẤP 2** | Multi-scale inference | ⚡⚡ (chi tiết tốt) | Trung bình | 1-2 giờ |
| 🟠 **CẤP 2** | Adaptive frame skipping | ⚡⚡ (cân bằng) | Trung bình | 1 giờ |
| 🟡 **CẤP 3** | Hierarchical K-means (màu) | ⚡ (màu chi tiết) | Khó | 2-3 giờ |
| 🟡 **CẤP 3** | Multi-stage OCR (fallback) | ⚡ (OCR +5-10%) | Khó | 1-2 giờ |

---

## ✅ Lợi ích dự kỳ sau các cải tiến

| Metric | Hiện tại | Sau cải tiến | Tăng |
|--------|---------|--------------|------|
| **Nhận diện màu chính xác** | ~75-80% | ~90-95% | **+15-20%** |
| **Frame processing** | 30 fps (all) | 6 fps (xử lý) | **5x nhanh** |
| **Biển số chính xác** | ~85-90% | ~95%+ | **+5-10%** |
| **GPU latency** | 50-80ms | 20-30ms | **2-3x nhanh** |
| **VRAM sử dụng** | ~4-5 GB | ~2-3 GB | **Giảm 50%** |

---

## 🔧 Quy trình cập nhật đề xuất

### Phase 1: Quick wins (1-2 giờ)
1. ✅ Cập nhật `config.py` (SKIP_FRAMES, TensorRT)
2. ✅ Cập nhật `color_analyzer.py` (CLAHE, kmeans iterations)
3. ✅ Test & validate

### Phase 2: Medium effort (3-4 giờ)
4. ✅ Thêm multi-scale inference trong `engine.py`
5. ✅ Thêm adaptive skipping logic
6. ✅ Test & validate

### Phase 3: Advanced (4-5 giờ)
7. ✅ Plate detection model integration
8. ✅ Temporal validation logic
9. ✅ Multi-stage OCR
10. ✅ Test & validate

### Phase 4: Polish (2-3 giờ)
11. ✅ Hierarchical K-means (nếu cần)
12. ✅ Performance tuning
13. ✅ Documentation

---

## 📝 Ghi chú

- **Backcompat**: Tất cả các cải tiến đều có fallback để giữ backcompat
- **Testing**: Sau mỗi phase cần test trên real video feeds
- **Dependencies**: Có thể cần thêm `pynvml` để GPU monitoring (optional)
- **Model files**: Cần download/train plate detection model (`yolo11n-plate.pt`)

---

**Cập nhật lần cuối**: May 15, 2026  
**Trạng thái**: Ready for implementation
