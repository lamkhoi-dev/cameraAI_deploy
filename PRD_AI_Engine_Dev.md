# 🤖 PRD — AI Engine: Đánh Giá & Đề Xuất Cải Thiện
## Tài liệu dành cho Dev AI | Version 1.0 | 02/05/2026

---

## 1. ĐÁNH GIÁ CODE HIỆN TẠI

### 1.1 Tổng quan vấn đề

| Module | Code hiện tại | Vấn đề chính | Mức độ |
|---|---|---|---|
| **Person Detection** | YOLOv8n-pose (5MB, mAP ~37%) | Model nano quá yếu, bỏ sót nhiều | 🟡 Upgrade |
| **Person Attributes** | K-means clustering trên raw pixels | Không phải AI model, dễ sai do ánh sáng | 🟡 Upgrade |
| **Vehicle Detection** | YOLOv8n COCO pretrained | Nano quá yếu, không custom train | 🟡 Upgrade |
| **License Plate** | Crop 35% dưới ảnh + EasyOCR | Không có model detect biển số, OCR yếu | 🔴 Rewrite |
| **Fire/Smoke** | HSV color thresholding | KHÔNG phải AI, false positive cực cao | 🔴 Rewrite |
| **Integration** | Lưu file text, không gọi API | Không kết nối với backend/DB | 🔴 Rewrite |
| **Multi-camera** | Hardcode `video1.mov` | Không đọc từ camera thực | 🔴 Rewrite |

### 1.2 Chi tiết từng module

#### ❌ Fire/Smoke — Vấn đề nghiêm trọng nhất

```python
# Code hiện tại (main.py:399-461) — CHỈ LÀ COLOR FILTER, KHÔNG PHẢI AI
lower_red1 = np.array([0, 120, 120])
upper_red1 = np.array([30, 255, 255])
fire_mask = cv2.inRange(hsv, lower_red1, upper_red1)
```

**Hậu quả**: Mọi vật thể màu đỏ/cam/vàng đều bị detect là "lửa" — áo đỏ, đèn vàng, sunset, biển hiệu...

#### ❌ License Plate — Crop thủ công

```python
# Code hiện tại (main.py:321-349) — KHÔNG CÓ AI DETECTION
plate_region_y_start = int(h * 0.65)  # Chỉ cắt 35% phía dưới ảnh xe
license_plate = vehicle_crop[plate_region_y_start:plate_region_y_end, ...]
```

**Hậu quả**: Biển số không ở vị trí cố định, xe từ góc nghiêng sẽ miss hoàn toàn.

#### ⚠️ Person Attributes — K-means thô

```python
# Code hiện tại (main.py:97-124)
_, labels, centers = cv2.kmeans(pixels, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
```

**Hậu quả**: Bóng đổ, nền xung quanh, ánh sáng đều ảnh hưởng kết quả màu.

#### ⚠️ Không integrate với Backend

```python
# db_integration.py TỒN TẠI nhưng main.py KHÔNG import nó
# main.py chỉ lưu file:
cv2.imwrite(f'{person_dir}/{crop_name}.jpg', crop_img)
# → Kết quả AI KHÔNG BAO GIỜ đến được Dashboard
```

---

## 2. ĐỀ XUẤT UPGRADE — CHI TIẾT TỪNG MODULE

---

### 2.1 MODULE 1: Person Detection + Tracking

#### Đề xuất: YOLOv11s-pose thay YOLOv8n-pose (Tesla P4 optimized)

| | YOLOv8n (hiện tại) | **YOLOv11s (đề xuất)** | YOLOv11m (nếu upgrade GPU) |
|---|---|---|---|
| **mAP** | ~37% | **~46.9%** | ~51.4% |
| **Size** | 5MB | **18MB** | 39MB |
| **Speed (Tesla P4 TRT FP16)** | ~4ms | **~6ms** | ~12ms |
| **VRAM** | ~0.3GB | **~0.8GB** | ~1.5GB |

**Lý do chọn YOLOv11s (thay vì m):**
- Tesla P4 chỉ có **8GB VRAM** → model m chiếm quá nhiều cho 4 models đồng thời
- mAP vẫn tăng **+10%** so với v8n → cải thiện rõ rệt
- TensorRT FP16 trên P4: ~6ms/frame → đủ cho 20 cameras @ 3fps
- Ultralytics API 100% tương thích, chỉ đổi model file

**Code thay đổi (1 dòng):**
```python
# Trước:
model_pose = YOLO('yolov8n-pose.pt')
# Sau (PyTorch):
model_pose = YOLO('yolo11s-pose.pt')
# Sau (TensorRT — BẮT BUỘC trên Tesla P4):
model_pose = YOLO('yolo11s-pose.engine')
```

**Tracking**: Giữ ByteTrack (đã tích hợp trong ultralytics `model.track()`)

---

### 2.2 MODULE 2: Person Attribute Recognition

#### Đề xuất: Thay K-means bằng pipeline 2 bước

**Bước 1**: Dùng YOLO crop chính xác vùng áo/quần (semantic segmentation hoặc keypoint-based)

**Bước 2**: Phân tích màu trên vùng đã crop sạch — loại bỏ nền

**Cải thiện K-means hiện tại (effort thấp, hiệu quả tốt):**

```python
def analyze_colors_improved(crop_img, part_name, num_colors=3):
    """Phiên bản cải thiện — loại bỏ nền trước khi K-means"""
    if crop_img is None or crop_img.size == 0:
        return None

    # 1. Loại bỏ viền ngoài (20% mỗi cạnh) — giảm noise từ nền
    h, w = crop_img.shape[:2]
    margin_x = int(w * 0.15)
    margin_y = int(h * 0.1)
    center_crop = crop_img[margin_y:h-margin_y, margin_x:w-margin_x]

    # 2. Loại bỏ pixel quá tối (shadow) và quá sáng (overexposed)
    hsv = cv2.cvtColor(center_crop, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, (0, 20, 40), (179, 255, 230))
    filtered = center_crop[mask > 0]

    if len(filtered) < 50:
        filtered = center_crop.reshape(-1, 3)

    # 3. K-means trên filtered pixels
    pixels = np.float32(filtered)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 15, 1.0)
    _, labels, centers = cv2.kmeans(pixels, num_colors, None, criteria, 10, cv2.KMEANS_PP_CENTERS)

    # 4. Sort by frequency
    label_counts = np.bincount(labels.flatten())
    sorted_idx = np.argsort(-label_counts)
    centers = np.uint8(centers)[sorted_idx]

    return centers  # Top-N dominant colors
```

**Nâng cao hơn (Phase 2):** Dùng Pedestrian Attribute Recognition model (PAR) — pre-trained trên PA-100K dataset, nhận diện 26 thuộc tính (giới tính, tuổi, loại áo, màu áo, loại quần, màu quần, phụ kiện...).

---

### 2.3 MODULE 3: Vehicle Detection + Classification

#### Đề xuất: YOLOv11s thay YOLOv8n (Tesla P4 optimized)

```python
# Trước:
model_object = YOLO('yolov8n.pt')
# Sau (TensorRT — BẮT BUỘC trên Tesla P4):
model_object = YOLO('yolo11s.engine')
```

**Cải thiện phân loại xe:**
- COCO classes phân biệt: car (2), motorcycle (3), bus (5), truck (7), bicycle (1) → **OK cho Phase 1**
- Phase 2: Fine-tune trên dataset xe Việt Nam nếu cần phân biệt xe tải nhỏ/lớn

---

### 2.4 MODULE 4: License Plate Detection + OCR

#### Đề xuất: Pipeline 2 bước thay vì crop thủ công

**Bước 1 — Detect biển số bằng YOLO custom:**
- Tải dataset biển số VN từ Roboflow Universe
- Fine-tune YOLOv11n (nano đủ vì biển số là object rõ ràng)
- Output: bounding box chính xác vùng biển số

**Bước 2 — OCR bằng PaddleOCR thay EasyOCR:**

| | EasyOCR (hiện tại) | PaddleOCR (đề xuất) |
|---|---|---|
| **Accuracy** | Trung bình | Cao hơn đáng kể |
| **Vietnamese** | Hỗ trợ | Hỗ trợ tốt hơn |
| **Speed** | Chậm hơn | Nhanh hơn |
| **Maintenance** | Ít update | Cập nhật thường xuyên (PP-OCRv5) |
| **Zero-result rate** | Cao | Thấp |

**Code mẫu pipeline biển số:**
```python
from ultralytics import YOLO
from paddleocr import PaddleOCR
import re

# Models
plate_detector = YOLO('models/plate_detect_yolo11n.pt')  # Custom trained
ocr = PaddleOCR(use_angle_cls=True, lang='vi', use_gpu=True)

# Vietnamese plate regex: 29A-123.45 hoặc 72C-98765
VN_PLATE_REGEX = r'^[0-9]{2}[A-Z][0-9]?[\-\s]?[0-9]{3,5}\.?[0-9]{0,2}$'

def detect_and_read_plate(vehicle_crop):
    # Step 1: Detect plate location
    results = plate_detector.predict(vehicle_crop, conf=0.5, verbose=False)
    if not results[0].boxes or len(results[0].boxes) == 0:
        return None

    # Step 2: Crop plate region
    box = results[0].boxes[0].xyxy[0].cpu().numpy().astype(int)
    plate_crop = vehicle_crop[box[1]:box[3], box[0]:box[2]]

    # Step 3: OCR
    ocr_result = ocr.ocr(plate_crop, cls=True)
    if not ocr_result or not ocr_result[0]:
        return None

    # Step 4: Combine + validate
    text = ''.join([line[1][0] for line in ocr_result[0]])
    conf = min([line[1][1] for line in ocr_result[0]])

    # Validate against VN plate format
    cleaned = re.sub(r'[^A-Z0-9\-\.]', '', text.upper())
    if re.match(VN_PLATE_REGEX, cleaned):
        return {'text': cleaned, 'confidence': conf, 'valid': True}
    return {'text': text, 'confidence': conf, 'valid': False}
```

---

### 2.5 MODULE 5: Fire & Smoke Detection ⚠️ QUAN TRỌNG NHẤT

#### Đề xuất: Thay HSV bằng YOLO custom model

**Phương án (effort thấp → cao):**

| Phương án | Effort | Accuracy | Ghi chú |
|---|---|---|---|
| **A) Tải pretrained từ HuggingFace** | 1 ngày | 70-80% | Tìm `yolo11-firedetect` trên HF |
| **B) Fine-tune YOLO11s trên Roboflow dataset** | 3-5 ngày | 85-90% | Dataset "fire smoke" ~10K images |
| **C) Custom dataset + train** | 2-3 tuần | 90%+ | Thu thập data từ môi trường thực |

**Đề xuất: Phương án B — Fine-tune**

```python
from ultralytics import YOLO

# 1. Tải dataset từ Roboflow
from roboflow import Roboflow
rf = Roboflow(api_key="YOUR_KEY")
project = rf.workspace("fire-smoke").project("fire-smoke-detection")
dataset = project.version(1).download("yolov11")

# 2. Train (RTX 3060, ~2-4 giờ)
model = YOLO('yolo11s.pt')  # Small model, tốt cho fire detection
model.train(
    data=f'{dataset.location}/data.yaml',
    epochs=100,
    imgsz=640,
    batch=16,
    device=0
)

# 3. Sử dụng
fire_model = YOLO('runs/detect/train/weights/best.pt')
results = fire_model.predict(frame, conf=0.5)
# Classes: ['fire', 'smoke']
```

**Giữ temporal filtering** hiện tại (3 frame liên tục) — logic đúng, chỉ thay detection method.

---

### 2.6 MODULE 6: Integration với Backend API

#### Đề xuất: Tích hợp `db_integration.py` + tái cấu trúc `main.py`

**Kiến trúc mới cho AI Engine:**

```
ai_engine/
├── __init__.py
├── engine.py              # Main orchestrator
├── config.py              # Cấu hình tập trung
├── models/                # Model weights (.pt) + TensorRT engines (.engine)
│   ├── yolo11s-pose.pt    → export → yolo11s-pose.engine
│   ├── yolo11s.pt         → export → yolo11s.engine
│   ├── fire_smoke_n.pt    → export → fire_smoke_n.engine
│   └── plate_detect_n.pt  → export → plate_detect_n.engine
├── processors/
│   ├── person_processor.py    # Detect + track + attributes
│   ├── vehicle_processor.py   # Detect + classify + plate
│   ├── fire_processor.py      # Fire/smoke detection
│   └── base_processor.py      # Base class
├── utils/
│   ├── color_analyzer.py      # Improved color analysis
│   ├── plate_reader.py        # PaddleOCR integration
│   └── frame_grabber.py       # Lấy frame từ go2rtc
└── api_client.py              # Gọi Backend API để push results
```

**`api_client.py` — Push results lên Backend:**

```python
import httpx
import asyncio
from typing import List, Dict

class AIResultClient:
    """Gửi kết quả AI lên Backend API"""

    def __init__(self, backend_url: str, api_key: str):
        self.backend_url = backend_url
        self.headers = {"X-API-Key": api_key}
        self.client = httpx.AsyncClient(timeout=10)

    async def push_persons(self, camera_id: str, frame_idx: int, persons: List[Dict]):
        await self.client.post(
            f"{self.backend_url}/api/ai/persons",
            json={
                "camera_id": camera_id,
                "frame_index": frame_idx,
                "persons": persons
            },
            headers=self.headers
        )

    async def push_alert(self, camera_id: str, alert_type: str, **kwargs):
        await self.client.post(
            f"{self.backend_url}/api/ai/alerts",
            json={"camera_id": camera_id, "alert_type": alert_type, **kwargs},
            headers=self.headers
        )
```

**`frame_grabber.py` — Lấy frame từ go2rtc:**

```python
import cv2
import threading
from collections import deque

class FrameGrabber:
    """Lấy frame từ go2rtc RTSP internal stream"""

    def __init__(self, camera_id: str, go2rtc_url: str = "localhost"):
        self.url = f"rtsp://{go2rtc_url}:8554/{camera_id}"
        self.frame = None
        self.running = False
        self._lock = threading.Lock()

    def start(self):
        self.running = True
        threading.Thread(target=self._capture_loop, daemon=True).start()

    def _capture_loop(self):
        cap = cv2.VideoCapture(self.url)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        while self.running:
            ret, frame = cap.read()
            if ret:
                with self._lock:
                    self.frame = frame
        cap.release()

    def get_frame(self):
        with self._lock:
            return self.frame.copy() if self.frame is not None else None

    def stop(self):
        self.running = False
```

---

## 3. PHÂN TÍCH PHẦN CỨNG PRODUCTION

### 3.1 Cấu hình Server: Dell R630

```
┌────────────────────────────────────────────────────────────┐
│  Dell PowerEdge R630 — Production Server                   │
├────────────────────────────────────────────────────────────┤
│  CPU:  2 × E5-2683V4 (16C/32T, 2.1-3.0GHz, 40MB Cache)  │
│        → Tổng: 32 Cores / 64 Threads                      │
│  RAM:  4 × 16GB DDR4 2133MHz → 64GB                       │
│  GPU:  Tesla P4 8GB GDDR5 (Pascal, Compute 6.1)           │
│  Disk: 3 × 1TB SAS (RAID 5 → ~2TB usable)                │
│        2 × 120GB SSD Samsung                               │
│  NIC:  4 × 1Gb Ethernet                                   │
│  PSU:  2 × 750W (redundant)                               │
└────────────────────────────────────────────────────────────┘
```

### 3.2 ⚠️ CẢNH BÁO QUAN TRỌNG — Tesla P4 Compatibility

> **Tesla P4 là GPU Pascal (2016) — đang bị deprecate bởi NVIDIA.**

| Component | Tình trạng hỗ trợ Tesla P4 |
|---|---|
| **NVIDIA Driver** | ✅ Vẫn hỗ trợ bởi driver hiện tại |
| **CUDA Toolkit** | ⚠️ Hỗ trợ trong CUDA 12.x — **SẼ BỊ BỎ ở CUDA 13.0** |
| **PyTorch** | ⚠️ **PHẢI dùng PyTorch ≤ 2.7** — bản 2.8+ đã bỏ Pascal |
| **Ultralytics** | ⚠️ Phụ thuộc PyTorch — phải pin version |
| **TensorRT** | ✅ Hỗ trợ FP16 + INT8 trên Pascal |

**→ BẮT BUỘC: Pin dependency versions trong Docker image:**
```dockerfile
# Dockerfile cho AI Engine — Tesla P4 compatible
FROM nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04

# Pin PyTorch 2.7 (last version supporting Pascal)
RUN pip install torch==2.7.0 torchvision==0.22.0 --index-url https://download.pytorch.org/whl/cu124
RUN pip install ultralytics>=8.3.0,<9.0.0
```

### 3.3 GPU Budget — Tesla P4 8GB VRAM

**VRAM chỉ có 8GB** → Phải chọn model size cẩn thận:

| Model | Size (VRAM) | PyTorch FP32 | TensorRT FP16 | TensorRT INT8 |
|---|---|---|---|---|
| YOLO11n (Person/Vehicle) | ~0.3GB | ~8ms | ~4ms | ~3ms |
| **YOLO11s (Person/Vehicle)** | **~0.8GB** | **~12ms** | **~6ms** | **~4ms** |
| YOLO11m (Person/Vehicle) | ~1.5GB | ~25ms | ~12ms | ~8ms |
| YOLO11l (Person/Vehicle) | ~2.0GB | ~40ms | ~18ms | ~12ms |

**Đề xuất thay đổi từ bản trước:**

| Model | Trước (RTX 3060 12GB) | **Nay (Tesla P4 8GB)** | Lý do |
|---|---|---|---|
| Person detect | YOLO11m-pose | **YOLO11s-pose** | Tiết kiệm VRAM, vẫn tốt hơn v8n |
| Vehicle detect | YOLO11m | **YOLO11s** | mAP 46.9% (vs 39.4% nano) |
| Fire detect | YOLO11s | **YOLO11n custom** | Fire/smoke ít class → nano đủ |
| Plate detect | YOLO11n | YOLO11n | Giữ nguyên |
| OCR | PaddleOCR GPU | **PaddleOCR CPU** | Giải phóng VRAM cho YOLO |

**VRAM Budget (Tesla P4 8GB):**

| Model | VRAM (TensorRT FP16) |
|---|---|
| YOLO11s-pose (Person) | ~0.8GB |
| YOLO11s (Vehicle) | ~0.8GB |
| YOLO11n (Fire/Smoke) | ~0.3GB |
| YOLO11n (License Plate) | ~0.3GB |
| CUDA overhead + buffers | ~1.0GB |
| **Tổng** | **~3.2GB / 8GB ✅** |

> **Còn ~4.8GB trống** cho batch processing, frame buffers, và headroom an toàn.

### 3.4 TensorRT Export — BẮT BUỘC (không optional như trước)

Trên Tesla P4, **TensorRT là bắt buộc** để đạt real-time. PyTorch thuần sẽ quá chậm:

```python
from ultralytics import YOLO

# Export all models to TensorRT FP16 (chạy 1 lần trên server)
for model_name in ['yolo11s-pose.pt', 'yolo11s.pt', 'fire_smoke_n.pt', 'plate_n.pt']:
    model = YOLO(model_name)
    model.export(format='engine', device=0, imgsz=640, half=True)
    # Output: yolo11s-pose.engine, yolo11s.engine, ...

# Sử dụng:
model = YOLO('yolo11s-pose.engine')  # Load TensorRT engine
results = model.predict(frame, verbose=False)
```

**Speed comparison trên Tesla P4 (ước tính):**

| Format | YOLO11s inference | Tăng tốc |
|---|---|---|
| PyTorch FP32 | ~25ms | 1x (baseline) |
| TensorRT FP16 | ~8ms | 3x |
| TensorRT INT8 | ~5ms | 5x |

### 3.5 Chiến lược xử lý 20 cameras — Tesla P4

```
STRATEGY: Hybrid GPU + CPU, Frame Skipping, Round-Robin

════════════════════════════════════════════════════════
GPU (Tesla P4): YOLO detection only
CPU (32C/64T):  Color analysis, OCR, pre/post processing, API calls
════════════════════════════════════════════════════════

20 cameras × 30fps (từ go2rtc)
→ AI xử lý 2-3 fps/camera (skip 10-15 frames)
→ 20 × 3fps = 60 frames/giây cần GPU inference

Pipeline per frame:
  [GPU] Person detect (TRT FP16):  ~8ms
  [GPU] Vehicle detect (TRT FP16): ~8ms   → CÓ THỂ BATCH cùng person
  [GPU] Fire detect (TRT FP16):    ~4ms   → Skip: chạy mỗi 3 frame
  [CPU] Color analysis (K-means):  ~5ms   → 32 cores xử lý song song
  [CPU] PaddleOCR (plate):         ~20ms  → Chỉ khi detect được biển số
  [CPU] API push (async):          ~2ms   → Non-blocking
  ─────────────────────────────────────
  GPU total per frame:             ~16ms  (person + vehicle + fire)
  → Max GPU throughput: 1000/16 = ~62 fps

Kết quả: 20 cameras × 3fps = 60 fps → VỪA ĐỦ ✅

NẾU CẦN THÊM THROUGHPUT:
  1. TensorRT INT8 thay FP16 → ~10ms/frame → 100 fps
  2. Giảm imgsz: 640 → 480 → tăng ~40% speed
  3. Fire detect chạy mỗi 5 frame thay 3
  4. Batch 2-4 frames cùng lúc (GPU sẽ efficient hơn)
```

### 3.6 Tận dụng CPU — 32 Cores / 64 Threads

> **Điểm mạnh của server này là CPU cực khỏe.** Phân công:

| Task | Hardware | Ghi chú |
|---|---|---|
| YOLO inference (detect/track) | **GPU** | TensorRT FP16/INT8 |
| Frame grabbing (20 cameras) | **CPU** (20 threads) | 1 thread/camera |
| Color analysis (K-means) | **CPU** (multiprocess) | Không cần GPU |
| PaddleOCR | **CPU** | Giải phóng GPU VRAM |
| API calls (push results) | **CPU** (async) | httpx async |
| go2rtc streaming | **CPU** | Binary riêng |
| PostgreSQL | **CPU** | Trên SSD |
| Pre-processing (resize, crop) | **CPU** | OpenCV |

**RAM Budget (64GB):**

| Component | RAM Usage |
|---|---|
| OS + system | ~2GB |
| PostgreSQL | ~2GB |
| go2rtc (20 streams) | ~1GB |
| AI Engine (Python + models) | ~4GB |
| Frame buffers (20 × 1080p) | ~2GB |
| PaddleOCR model | ~0.5GB |
| Backend (FastAPI) | ~0.5GB |
| Frontend build | ~0.3GB |
| Docker overhead | ~1GB |
| **Tổng** | **~13GB / 64GB ✅** |

> **Kết luận RAM: Rất thoải mái.** Có thể dùng RAM dư để cache frames.

---

## 4. CHECKLIST CÔNG VIỆC CHO DEV AI

### Phase 1 — MVP (2-3 tuần)

```
Week 1: Setup + Core Pipeline
- [ ] Setup Docker image với PyTorch 2.7 + CUDA 12.4 (Tesla P4 compatible)
- [ ] Download YOLO11s-pose.pt + YOLO11s.pt (thay nano)
- [ ] ⚠️ Export TensorRT FP16 engines trên server (BẮT BUỘC cho Tesla P4)
- [ ] Tích hợp FrameGrabber — đọc frame từ go2rtc RTSP
- [ ] Tích hợp APIClient — push results lên backend /api/ai/*
- [ ] Test pipeline: camera → AI → API → Dashboard hiển thị

Week 2: Fire Detection + Color
- [ ] Fire/Smoke: Tải pretrained hoặc fine-tune YOLO11n
- [ ] Thay HSV detection bằng YOLO fire model
- [ ] Export fire model → TensorRT engine
- [ ] Cải thiện color analysis (loại bỏ nền, shadow)
- [ ] Test fire detection — đo false positive rate

Week 3: License Plate + Refactor
- [ ] License Plate: Train YOLO11n detect biển số VN
- [ ] Tích hợp PaddleOCR (CPU mode) thay EasyOCR
- [ ] Tái cấu trúc main.py → ai_engine/ package
- [ ] Multi-camera test: 4-8 cameras đồng thời trên Tesla P4
- [ ] Benchmark: đo GPU VRAM, FPS, temperature dưới load
```

### Phase 2 — Nâng cao (sau nghiệm thu Phase 1)

```
- [ ] FaceID: Tích hợp ArcFace/InsightFace
- [ ] Pedestrian Attribute Recognition model
- [ ] pgvector cho face vector search
- [ ] TensorRT INT8 (tăng speed thêm ~60% so FP16)
- [ ] Scale test: 16-20 cameras đồng thời
- [ ] SAHI cho camera resolution cao (4K)
- [ ] Monitoring: GPU temp, VRAM usage, FPS dashboard
```

---

## 5. API CONTRACT — GIAO DIỆN GIỮA 2 NHÁNH DEV

> **Quy ước**: Dev AI gọi các endpoint dưới đây để push kết quả. Backend (nhánh bạn) sẽ nhận, lưu DB, push WebSocket.

### POST /api/ai/persons

```json
{
  "camera_id": "cam_01",
  "frame_index": 1234,
  "timestamp": "2026-05-02T10:30:00Z",
  "persons": [
    {
      "track_id": 5,
      "confidence": 0.92,
      "bbox": [100, 200, 300, 450],
      "attributes": {
        "shirt_colors": [{"rank": 1, "name": "Trắng", "rgb": [255,255,255]}],
        "pants_colors": [{"rank": 1, "name": "Đen", "rgb": [0,0,0]}],
        "hair_colors": [{"rank": 1, "name": "Đen", "rgb": [10,10,10]}]
      },
      "crop_path": "cropped_data/person_5/full_body.jpg"
    }
  ]
}
```

### POST /api/ai/vehicles

```json
{
  "camera_id": "cam_01",
  "frame_index": 1235,
  "timestamp": "2026-05-02T10:30:01Z",
  "vehicles": [
    {
      "track_id": 12,
      "vehicle_type": "car",
      "confidence": 0.94,
      "bbox": [400, 300, 700, 550],
      "colors": [{"rank": 1, "name": "Bạc", "rgb": [192,192,192]}],
      "license_plate": {
        "text": "29A-12345",
        "confidence": 0.87,
        "valid": true
      },
      "crop_path": "cropped_data/vehicles/car/frame_1235.jpg"
    }
  ]
}
```

### POST /api/ai/alerts

```json
{
  "camera_id": "cam_01",
  "frame_index": 5678,
  "timestamp": "2026-05-02T10:35:00Z",
  "alert_type": "fire",
  "severity": "high",
  "confidence": 0.87,
  "description": "Fire detected",
  "bbox": [50, 300, 400, 600],
  "snapshot_path": "cropped_data/fire_alerts/frame_5678.jpg"
}
```

### POST /api/ai/heartbeat

```json
{
  "status": "running",
  "cameras_processing": ["cam_01", "cam_02", "cam_03"],
  "fps_avg": 8.5,
  "gpu_usage_percent": 65,
  "models_loaded": ["yolo11m-pose", "yolo11m", "fire_smoke", "plate_detect"]
}
```

---

## 6. REQUIREMENTS.TXT (CẬP NHẬT)

```txt
# AI & Computer Vision
ultralytics>=8.3.0,<9.0.0  # YOLO11 support
torch==2.7.0               # ⚠️ PINNED — last version supporting Tesla P4 (Pascal)
torchvision==0.22.0        # Match torch 2.7
opencv-python>=4.10.0
numpy>=1.24.0,<2.0.0

# OCR (thay EasyOCR — chạy trên CPU)
paddlepaddle>=2.6.0        # CPU version — giải phóng GPU VRAM
paddleocr>=2.9.0

# API Client
httpx>=0.27.0              # Async HTTP client

# Utilities
python-dotenv>=1.0.0

# Optional (Phase 2)
# insightface>=0.7.0       # FaceID
# faiss-cpu>=1.7.0          # Vector search (CPU vì GPU VRAM hạn chế)
# onnxruntime>=1.17.0       # TensorRT alternative
```

**Loại bỏ:**
- `easyocr` → thay bằng `paddleocr`
- `sahi` → chưa dùng (Phase 2)
- `flask*` → không cần trong AI engine (backend riêng)
- `paddlepaddle-gpu` → dùng CPU version để tiết kiệm VRAM

---

## 7. TÓM TẮT ĐỀ XUẤT (Cập nhật cho Tesla P4 8GB)

| Thay đổi | Effort | Impact | Priority |
|---|---|---|---|
| Setup Docker (PyTorch 2.7 + CUDA 12.4) | 0.5 ngày | Tesla P4 compatibility | 🔴 Bắt buộc |
| YOLOv8n → **YOLOv11s** (person + vehicle) | **1 dòng code** | mAP +10% | 🟢 Làm ngay |
| **Export TensorRT FP16** (tất cả models) | 0.5 ngày | Speed x3 (bắt buộc trên P4) | 🔴 Bắt buộc |
| Tích hợp FrameGrabber (đọc từ go2rtc) | 1 ngày | Kết nối camera thực | 🟢 Làm ngay |
| Tích hợp APIClient (push lên backend) | 1 ngày | Data tới Dashboard | 🟢 Làm ngay |
| HSV → YOLO fire model | 3-5 ngày | Giảm 90% false positive | 🟢 Ưu tiên cao |
| Crop thủ công → YOLO plate detect | 3-5 ngày | Detect chính xác biển số | 🟡 Phase 1 |
| EasyOCR → PaddleOCR (**CPU mode**) | 1 ngày | OCR accuracy tăng, VRAM free | 🟡 Phase 1 |
| Cải thiện K-means (loại nền) | 0.5 ngày | Màu sắc chính xác hơn | 🟡 Phase 1 |
| Refactor main.py → package | 2-3 ngày | Maintainable, testable | 🟡 Phase 1 |
| FaceID (ArcFace) | 1-2 tuần | Nhận diện khuôn mặt | 🔵 Phase 2 |
| TensorRT INT8 | 0.5 ngày | Speed thêm +60% | 🔵 Phase 2 |
